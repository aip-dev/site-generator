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

from __future__ import annotations

import click

from aip_site import server
from aip_site.publisher import Publisher


@click.command()
@click.argument('src', type=click.Path(
    allow_dash=False,
    dir_okay=True,
    exists=True,
    file_okay=False,))
@click.argument('dest', type=click.Path(
    allow_dash=False,
    dir_okay=True,
    exists=False,
    file_okay=False,
    writable=True))
def publish(src: str, dest: str):
    """Publish static HTML pages into the specified location."""
    publisher = Publisher(src, dest)
    publisher.publish_site()


@click.command()
@click.argument('src', type=click.Path(
    allow_dash=False,
    dir_okay=True,
    exists=True,
    file_okay=False))
def serve(src: str):
    """Run a debug server."""
    server.app.before_request(server.site_load_func(src))
    server.app.run(host='0.0.0.0', port=4000, debug=True)
