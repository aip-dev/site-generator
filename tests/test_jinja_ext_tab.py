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

import textwrap

import jinja2

from aip_site.jinja.ext.tab import TabExtension


def test_tab():
    t = jinja2.Template(textwrap.dedent("""
        {% tab proto %}
        Something something
        More more more
        {% endtabs %}
    """), extensions=[TabExtension])
    rendered = t.render()
    assert '=== "Protocol buffers"' in rendered
    assert '  Something something\n' in rendered
    assert '  More more more\n' in rendered


def test_multiple_tabs():
    t = jinja2.Template(textwrap.dedent("""
        {% tab proto %}
        Something something
        {% tab oas %}
        Something else
        {% endtabs %}
    """), extensions=[TabExtension])
    rendered = t.render()
    assert '=== "Protocol buffers"' in rendered
    assert '=== "OpenAPI 3.0"' in rendered
