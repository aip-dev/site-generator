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

import os

import jinja2
import jinja2.ext
import jinja2.nodes

from aip_site import md


TEMPLATE_DIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), 'support', 'templates'),
)


class TabExtension(jinja2.ext.Extension):
    tags = {'tab'}

    def parse(self, parser, cursor=()):
        # The first token is the token that started the tag, which is always
        # "tab" because that is the only token we watch.
        lineno = next(parser.stream).lineno

        # Get the language for this tab.
        lang = parser.stream.expect('name')
        lang_title = {
            'oas': 'OpenAPI 3.0',
            'proto': 'Protocol buffers',
        }.get(lang.value, lang.value.capitalize())

        # Encase the tab's content in a Markdown tab, properly indented.
        # WRONG NODE: Need to determine the right one.
        tab_title = jinja2.nodes.TemplateData(f'=== "{lang_title}"\n\n')
        body = parser.parse_statements(['name:endtabs', 'name:tab'])
        indented_body = jinja2.nodes.FilterBlock(
            body,
            jinja2.nodes.Filter(
                None, 'indent', (), [
                    jinja2.nodes.Keyword('width', jinja2.nodes.Const(2)),
                    jinja2.nodes.Keyword('first', jinja2.nodes.Const(True)),
                ], None, None,
            ),
        ).set_lineno(lineno)
        cursor += (tab_title, indented_body)

        # If there is another tab, parse it too.
        if parser.stream.current.value == 'tab':
            return self.parse(parser, cursor=cursor)
        else:
            next(parser.stream)  # Drop endtabs.

        # Done; return the content.
        return list(cursor)


class SampleExtension(jinja2.ext.Extension):
    tags = {'sample'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        args = parser.parse_tuple()
        return jinja2.nodes.Const('\n')


jinja_env = jinja2.Environment(
    extensions=[
        # SampleExtension,
        TabExtension,
    ],
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR),
    undefined=jinja2.StrictUndefined,
)
jinja_env.filters['markdown'] = lambda s: md.MarkdownDocument(s).html
