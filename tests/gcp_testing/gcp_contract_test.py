# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import unittest
from mock import Mock

from googleapiclient.errors import HttpError


from citest.base import (
    new_global_journal_with_path,
    ExecutionContext,
    JsonSnapshotHelper)

import citest.gcp_testing as gt
import citest.json_predicate as jp
import citest.json_contract as jc
import citest.service_testing as st
ov_factory = jc.ObservationPredicateFactory()

from tests.gcp_testing.test_gcp_agent import (
    FakeGcpService,
    TestGcpAgent)


class MyFakeGcpService(FakeGcpService):
  def __init__(self, execute_response_list):
    super(MyFakeGcpService, self).__init__(execute_response_list)
    self.regions = self

  def __call__(self):
    return self


class GcpContractTest(st.AgentTestCase):
  @property
  def testing_agent(self):
    return TestGcpAgent.make_test_agent()

  def test_empty_builder(self):
    context = ExecutionContext()
    agent = self.testing_agent
    contract_builder = gt.GcpContractBuilder(agent)
    contract = contract_builder.build()
    results = contract.verify(context)
    self.assertTrue(results)

  def test_list(self):
    context = ExecutionContext()
    default_variables = {'project': 'PROJECT'}
    service = MyFakeGcpService([{'items': [1, 2, 3]}])
    agent = TestGcpAgent.make_test_agent(
        service=service, default_variables=default_variables)

    contract_builder = gt.GcpContractBuilder(agent)
    c1 = contract_builder.new_clause_builder('TITLE')
    verifier = c1.list_resource('regions')
    verifier.contains_path_value(jp.DONT_ENUMERATE_TERMINAL, [1, 2, 3])

    # When we build and run the contract, it is going to call the observer.
    # The clause has no constraints so it will succeed. We do this so that
    # we can verify the contract will call the clause which in turn will
    # call the agent with the expected parameters we test for below.
    contract = contract_builder.build()
    self.assertTrue(contract.verify(context))
    self.assertEquals({'project': 'PROJECT'}, agent.service.last_list_args)

  def test_inspect_not_found_ok(self):
    context = ExecutionContext()
    response = Mock()
    response.status = 404
    response.reason = 'Not Found'
    default_variables = {'project': 'PROJECT'}
    service = MyFakeGcpService([HttpError(response, b'Not Found')])
    agent = TestGcpAgent.make_test_agent(
        service=service, default_variables=default_variables)


    contract_builder = gt.GcpContractBuilder(agent)

    c1 = contract_builder.new_clause_builder('TITLE')
    verifier = c1.inspect_resource('regions', resource_id='us-central1-f')
    verifier.EXPECT(
        ov_factory.error_list_contains(gt.HttpErrorPredicate(http_code=404)))
    self.assertTrue(isinstance(verifier, jc.ValueObservationVerifierBuilder))

    contract = contract_builder.build()
    verification_result = contract.verify(context)
    self.assertTrue(verification_result,
                    JsonSnapshotHelper.ValueToEncodedJson(verification_result))
    self.assertEquals({'project': 'PROJECT', 'region': 'us-central1-f'},
                      agent.service.last_get_args)

  def test_inspect_indirect(self):
    context = ExecutionContext(test_id='TESTID', test_project='PROJECT')
    default_variables = {'project': lambda x: x.get('test_project', 'UNKNOWN')}
    service = MyFakeGcpService(['Hello, World'])
    agent = TestGcpAgent.make_test_agent(
        service=service, default_variables=default_variables)

    contract_builder = gt.GcpContractBuilder(agent)

    c1 = contract_builder.new_clause_builder('TITLE')
    verifier = c1.inspect_resource(
        'regions', resource_id=lambda x: x['test_id'])
    verifier.EXPECT(ov_factory.value_list_contains(jp.STR_EQ('Hello, World')))
    self.assertTrue(isinstance(verifier, jc.ValueObservationVerifierBuilder))

    contract = contract_builder.build()
    verification_result = contract.verify(context)
    self.assertTrue(verification_result,
                    JsonSnapshotHelper.ValueToEncodedJson(verification_result))
    self.assertEquals({'project': 'PROJECT', 'region': 'TESTID'},
                      agent.service.last_get_args)


if __name__ == '__main__':
  new_global_journal_with_path('./gce_contract_test.journal')
  unittest.main()
