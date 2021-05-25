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
        symbols = []
        while parser.stream.look().type == 'string':
            parser.stream.expect('comma')
            symbols.append(parser.stream.expect('string').value)

        # Load the sample file.
        aip = self.environment.loader.aip
        filename = os.path.join(aip.path, fn)
        try:
            with io.open(filename, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            raise jinja2.TemplateSyntaxError(
                filename=parser.filename,
                lineno=lineno,
                message=f'File not found: {filename}',
            )

        # Tease out the desired symbols and make snippets.
        snippets = []
        for symbol in symbols:
            match = re.search(rf'^([\s]*)({symbol})', code, flags=re.MULTILINE)
            if not match:
                raise jinja2.TemplateSyntaxError(
                    filename=parser.filename,
                    lineno=lineno,
                    message=f'Symbol not found: {symbol}',
                )

            # Determine the end of the symbol.
            # This attempts to parse C-style brace syntax if it encounters a
            # `{` character, or Python/YAML-style indenting if it encounters a
            # `:` character.
            #
            # The first thing we need to know is which syntax we are using.
            # We attempt to guess that by seeing which token we encounter next
            # after our symbol.
            start = match.start()
            try:
                ix, block_token = sorted([
                    (loc + 1, i) for i in (':', '{', ';')
                    if (loc := code.find(i, match.end())) != -1])[0]
            except IndexError:
                raise jinja2.TemplateSyntaxError(
                    filename=filename,
                    lineno=code.count('\n', 0, start) - 1,
                    message=f'No block character (:, {{) found after {symbol}',
                )

            # Push the start marker backwards to include any leading comments.
            lines = code[0:start - 1].split('\n')
            for line in reversed(lines):
                if re.search(r'^[\s]*(//|#)', line):
                    start -= len(line) + 1
                else:
                    break

            # If we got a `:`, we parse by indentation, stopping at the
            # start of the next line with the same indentation as our match.
            snippet = ''
            if block_token == ':':
                indent = len(match.groups()[0])
                end_match = re.search(r'^[\s]{0,%d}[\S]+' % indent, code[ix:],
                    re.MULTILINE,
                )
                if end_match:
                    snippet = code[start:end_match.start() + ix]
                else:
                    snippet = code[start:]
                snippet = textwrap.dedent(snippet)

            # We got a '{'; Find the corresponding closed brace.
            elif block_token == '{':
                cursor = match.start()
                while (close_brace := code.find('}', cursor)) != -1:
                    s, e = match.start(), close_brace + 1
                    if code.count('{', s, e) == code.count('}', s, e):
                        snippet = textwrap.dedent(code[start:e])
                        break
                    cursor = e
                else:
                    # Unable to find a corresponding closed brace; complain.
                    raise jinja2.TemplateSyntaxError(
                        filename=filename,
                        message=f'No corresponding }} found for {symbol}.',
                        lineno=code.count('\n', 0, start) - 1,
                    )

            # We got a ';'. Stop there.
            else:
                end = code.find(';', match.start()) + 1
                snippet = textwrap.dedent(code[start:end])

            # Append the snippet to the list of snippets.
            snippets.append(snippet)

        # We have a snippet. Time to put the Markdown together.
        md = '\n'.join((
            '```{0}'.format(filename.split('.')[-1]),
            '\n\n'.join(snippets),
            '```',
        ))

        # Finally, return a node to display it.
        return jinja2.nodes.Output(
            [jinja2.nodes.TemplateData(md)],
        )
