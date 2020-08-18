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

import io
import os
import re
import textwrap

import jinja2.ext
import jinja2.nodes


class SampleExtension(jinja2.ext.Extension):
    tags = {'sample'}

    def parse(self, parser):
        # The first token is the token that started the tag, which is always
        # "sample" because that is the only token we watch.
        lineno = next(parser.stream).lineno

        # Get the sample to be loaded.
        # A sample includes both a filename and a symbol within that file,
        # which is what is shown in the output.
        fn = parser.stream.expect('string').value
        parser.stream.expect('comma')
        symbol = parser.stream.expect('string').value

        # Sanity check: Does the file exist?
        aip = self.environment.loader.aip
        filename = os.path.join(aip.path, fn)
        if not os.path.isfile(filename):
            raise jinja2.TemplateSyntaxError(
                filename=parser.filename,
                lineno=lineno,
                message='File not found: %s' % filename,
            )

        # Load the file.
        with io.open(filename, 'r') as f:
            code = f.read()

        # Tease out the desired symbol.
        match = re.search(rf'^([\s]*)({symbol})', code, flags=re.MULTILINE)
        if not match:
            raise jinja2.TemplateSyntaxError(
                filename=parser.filename,
                lineno=lineno,
                message=f'Symbol not found: {symbol}',
            )

        # Determine the end of the symbol.
        # This attempts to parse C-style brace syntax if it encounters a `{`
        # character, or Python/YAML-style indenting if it encounters a `:`.
        #
        # The first thing we need to know is which syntax we are using.
        # We attempt to guess that by seeing which token we encounter next
        # after our symbol.
        start = match.start()
        try:
            ix, block_token = sorted([
                (loc + 1, i) for i in (':', '{')
                if (loc := code.find(i, start)) != -1])[0]
        except IndexError:
            raise jinja2.TemplateSyntaxError(
                filename=filename,
                message=f'No block character (:, {{) found after {symbol}.',
                lineno=code.count('\n', 0, start) - 1,
            )

        # If we got a `:`, we parse by indentation, stopping at the beginning
        # of the next line with the same indentation as our match.
        snippet = ''
        if block_token == ':':
            indent = match.groups()[0]
            end_match = re.search(rf'^{indent}[\S]+', code[ix:], re.MULTILINE)
            if end_match:
                snippet = code[start:end_match.start() + ix]
            else:
                snippet = code[start:]
            snippet = textwrap.dedent(snippet)
        # We got a `{`; we find the corresponding closed brace.
        else:  # block_token == '{':
            cursor = start
            while (close_brace := code.find('}', cursor)) != -1:
                s, e = start, close_brace + 1
                if code.count('{', s, e) == code.count('}', s, e):
                    snippet = textwrap.dedent(code[s:e])
                    break
                cursor = e
            else:
                raise jinja2.TemplateSyntaxError(
                    filename=filename,
                    message=f'No corresponding }} found for {symbol}.',
                    lineno=code.count('\n', 0, start) - 1,
                )

        # We have a snippet. Time to put the Markdown together.
        md = '\n'.join((
            '```{0}'.format(filename.split('.')[-1]),
            snippet,
            '```',
        ))

        # Finally, return a node to display it.
        return jinja2.nodes.Output(
            [jinja2.nodes.TemplateData(md)],
        )
