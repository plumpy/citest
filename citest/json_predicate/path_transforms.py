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

"""Common transforms to use with PathPredicate that provide journaling."""

from citest.base import JsonSnapshotableEntity
from .path_value import PATH_SEP

class FieldDifference(JsonSnapshotableEntity):
  """Transform a dictionary value into the difference of two fields within."""

  @property
  def minuend(self):
    """The field name containing the value to subtract from."""
    return self.__minuend

  @property
  def subtractend(self):
    """The field name containing the value to subtract."""
    return self.__subtractend

  def  __init__(self, minuend, subtractend):
    """Constructor.

    Args:
      minuend: [string] The field of the value to subtract from.
      subtractend: [string] The field of the value to substract.
    """
    if not callable(minuend) and minuend.find(PATH_SEP) >= 0:
      raise ValueError('Nested fields are not yet supported.')
    if not callable(subtractend) and subtractend.find(PATH_SEP) >= 0:
      raise ValueError('Nested fields are not yet supported.')

    self.__minuend = minuend
    self.__subtractend = subtractend

  def __str__(self):
    return '("{0}" - "{1}")'.format(self.__minuend, self.__subtractend)

  def __eq__(self, transform):
    return (self.__class__ == transform.__class__
            and self.__minuend == transform.minuend
            and self.__subtractend == transform.subtractend)

  def export_to_json_snapshot(self, snapshot, entity):
    """Implements JsonSnapshotableEntity interface."""
    snapshot.edge_builder.make_control(
        entity, 'Operation',
        '{0} - {1}'.format(self.__minuend, self.__subtractend))

  def __call__(self, context, source):
    """Operator.

    Args:
      source: [dict] Contains the minuend and subtracted
    Returns:
      Value of minuend - subtractend
    """
    minuend_key = context.eval(self.__minuend)
    subtractend_key = context.eval(self.__subtractend)
    if minuend_key.find(PATH_SEP) >= 0:
      raise ValueError('Nested fields "{0}" are not yet supported.'
                       .format(minuend_key))
    if subtractend_key.find(PATH_SEP) >= 0:
      raise ValueError('Nested fields "{0}" are not yet supported.'
                       .format(subtractend_key))

    return  source[minuend_key] - source[subtractend_key]
