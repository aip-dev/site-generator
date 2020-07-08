# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import mock

from click.testing import CliRunner
import flask

from aip_site import cli
from aip_site.publisher import Publisher


def test_publish():
    runner = CliRunner()
    with mock.patch.object(Publisher, 'publish_site') as ps:
        result = runner.invoke(
            cli.publish,
            ['tests/test_data/', '/path/to/dest'],
        )
        ps.assert_called_once_with()
    assert result.exit_code == 0


def test_serve():
    runner = CliRunner()
    with mock.patch.object(flask.Flask, 'run') as run:
        result = runner.invoke(cli.serve, ['tests/test_data/'])
        run.assert_called_once_with(host='0.0.0.0', port=4000, debug=True)
    assert result.exit_code == 0
