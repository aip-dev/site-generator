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
import io
import textwrap

import jinja2
import pytest

from aip_site.jinja import loaders


def test_valid_sample(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'message Book' %}
        """)
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
        assert '```proto\n' in rendered
        assert 'message Book {' in rendered
        assert 'string name = 1;' in rendered


def test_valid_sample_nested_braces(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'message Book' %}
        """)
    content = textwrap.dedent("""
        // A representation for a book.
        message Book {
            string name = 1;
            enum Type {
                TYPE_UNSPECIFIED = 0;
                HARDCOVER = 1;
            }
            Type type = 2;
        }

        message Other {
            string whatever = 1;
        }
    """.lstrip())
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```proto\n' in rendered
    assert '// A representation for a book.\n' in rendered
    assert 'message Book {\n' in rendered
    assert '    string name = 1;\n' in rendered
    assert '    enum Type {\n' in rendered
    assert '        TYPE_UNSPECIFIED = 0;\n' in rendered
    assert '    Type type = 2;\n' in rendered
    assert 'message Other' not in rendered
    assert 'string whatever' not in rendered


def test_valid_sample_semi(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'string name' %}
        """)
    content = textwrap.dedent("""
        // A representation of a book.
        message Book {
            // The name of the book.
            // Format: publishers/{publisher}/books/{book}
            string name = 1;
        }
    """)
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```proto\n' in rendered
    assert '// The name of the book.' in rendered
    assert 'string name = 1;\n' in rendered
    assert '  string name = 1;\n' not in rendered
    assert '// A representation of a book.\n' not in rendered
    assert 'message Book {\n' not in rendered


def test_valid_sample_yaml(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.oas.yaml', 'paths' %}
        """)
    content = textwrap.dedent("""
        ---
        schemas:
            meh: meh
        # The paths.
        paths:
            foo: bar
            baz: bacon
        something_else: false
    """)
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```yaml\n' in rendered
    assert '# The paths.\n' in rendered
    assert 'paths:\n' in rendered
    assert '    foo: bar\n' in rendered
    assert '    baz: bacon\n' in rendered
    assert 'schemas:' not in rendered
    assert 'something_else:' not in rendered


def test_valid_sample_yaml_indented(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.oas.yaml', 'paths' %}
        """)
    content = textwrap.dedent("""
        ---
        schemas:
            meh: meh
            # The paths.
            paths:
                foo: bar
                baz: bacon
        something_else: false
    """)
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```yaml\n' in rendered
    assert '# The paths.\n' in rendered
    assert 'paths:\n' in rendered
    assert '    foo: bar\n' in rendered
    assert '    baz: bacon\n' in rendered
    assert 'schemas:' not in rendered
    assert 'something_else:' not in rendered


def test_valid_sample_yaml_with_braces(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.oas.yaml', '/v1/publishers/{publisherId}' %}
        """)
    content = textwrap.dedent("""
        ---
        paths:
            /v1/publishers/{publisherId}:
                baz: bacon
        something_else: false
    """).strip('\n')
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```yaml\n' in rendered
    assert 'paths:\n' not in rendered
    assert '/v1/publishers/{publisherId}:\n' in rendered
    assert '    baz: bacon\n' in rendered
    assert 'something_else:' not in rendered


def test_valid_sample_yaml_to_eof(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.oas.yaml', 'paths' %}
        """)
    content = textwrap.dedent("""
        ---
        paths:
            foo: bar
            baz: bacon
        schemas:
            meh: meh
    """)
    with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
        rendered = les_mis.env.get_template('test').render(aip=les_mis)
    assert '```yaml\n' in rendered
    assert 'paths:\n' in rendered
    assert '    foo: bar\n' in rendered
    assert '    baz: bacon\n' in rendered
    assert 'schemas:' not in rendered


def test_invalid_sample_file_not_found(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'bogus.proto', 'message Book' %}
        """)
    with pytest.raises(jinja2.TemplateSyntaxError) as ex:
        les_mis.env.get_template('test').render(aip=les_mis)
    assert ex.value.message.startswith('File not found: ')
    assert ex.value.message.endswith('bogus.proto')


def test_invalid_sample_symbol_not_found(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'message Movie' %}
        """)
    with pytest.raises(jinja2.TemplateSyntaxError) as ex:
        les_mis.env.get_template('test').render(aip=les_mis)
    assert ex.value.message.startswith('Symbol not found: ')
    assert ex.value.message.endswith('message Movie')


def test_invalid_sample_no_open_brace(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'message Book' %}
        """)
    with pytest.raises(jinja2.TemplateSyntaxError) as ex:
        content = 'message Book\n'
        with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
            les_mis.env.get_template('test').render(aip=les_mis)
    assert ex.value.message.startswith('No block character')
    assert ex.value.message.endswith('message Book')


def test_invalid_sample_no_close_brace(site):
    with mock.patch.object(loaders, 'AIPLoader', TestLoader):
        les_mis = site.aips[62]
        les_mis.env.loader.set_template_body(r"""
            {% sample 'les_mis.proto', 'message Book' %}
        """)
    with pytest.raises(jinja2.TemplateSyntaxError) as ex:
        content = 'message Book {\n'
        with mock.patch.object(io, 'open', mock.mock_open(read_data=content)):
            les_mis.env.get_template('test').render(aip=les_mis)
    assert ex.value.message.startswith('No corresponding }')
    assert ex.value.message.endswith('message Book.')


class TestLoader(loaders.AIPLoader):
    def set_template_body(self, text):
        self._body = textwrap.dedent(text)

    def list_templates(self):
        return super().list_templates() + ['test']

    def get_source(self, env, template):
        if template == 'test':
            return self._body, 'test.md.j2', None
        return super().get_source(env, template)
