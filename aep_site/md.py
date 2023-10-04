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

import re

import markdown              # type: ignore
import pymdownx.highlight    # type: ignore
import pymdownx.superfences  # type: ignore

from aip_site.utils import cached_property


class MarkdownDocument(str):
    """A utility class representing Markdown content."""

    def __init__(self, content: str, *, toc_title: str = 'Contents'):
        self._content = content
        self._engine = markdown.Markdown(
            extensions=[_superfences, 'tables', 'toc', 'pymdownx.tabbed'],
            extension_configs={
                'toc': {
                    'title': toc_title,
                    'toc_depth': '2-3',
                },
            },
            tab_length=2,
        )

    def __str__(self) -> str:
        return self._content

    @cached_property
    def blocked_content(self) -> str:
        """Return a Markdown document with Jinja blocks added per-section."""
        answer = str(self)

        # We need to fire the html property because conversion may not have
        # happened yet, and the toc extension requires conversion to occur
        # first.
        #
        # The `html` property caches, so this does not entail any additional
        # performance hit.
        self.html

        # We use the Markdown toc plugin to separate the headers and identify
        # where to put the blocks. Iterate over each toc_token and encapsulate
        # it in a block.
        toc_tokens = self._engine.toc_tokens  # type: ignore
        for ix, token in enumerate(toc_tokens):
            try:
                next_token = toc_tokens[ix + 1]
            except IndexError:
                next_token = None
            answer = _add_block(answer, token, next_token)

        # Done; return the answer.
        return answer

    @cached_property
    def html(self) -> str:
        """Return the HTML content for this Markdown document."""
        return self._engine.convert(self._content)

    @cached_property
    def title(self) -> str:
        """Return the document title."""
        return self._content.strip().splitlines()[0].strip('# \n')

    @property
    def toc(self) -> str:
        """Return a table of contents for the Markdown document."""
        # We need to fire the html property because conversion may not have
        # happened yet, and the toc extension requires conversion to occur
        # first.
        #
        # The `html` property caches, so this does not entail any additional
        # performance hit.
        self.html
        return self._engine.toc  # type: ignore


def _add_block(content: str, toc_token, next_toc_token=None) -> str:
    # Determine the beginning of the block.
    heading = '#' * toc_token['level'] + r'\s+' + toc_token['name']
    match = re.search(heading, content)
    if not match:
        return content
    start_ix = match.span()[0]

    # Determine the end of the block.
    end_ix = len(content)
    if next_toc_token:
        end_h = '#' * next_toc_token['level'] + r'\s+' + next_toc_token['name']
        match = re.search(end_h, content)
        if not match:
            return content
        end_ix = match.span()[0]
    elif '{% endblock %}' in content[start_ix:]:
        # We can match against an {% endblock %} safely because we are
        # processing "top-down" (e.g. <h2> before <h3>), then beginning-to-end;
        # this means that encountering an {% endblock %} is guaranteed to be
        # the endblock for the enclosing block.
        end_ix = content.index('{% endblock %}', start_ix)

    # Add the block for this heading.
    block = content[start_ix:end_ix]
    block_id = toc_token['id'].replace('-', '_')
    content = content.replace(block, '\n'.join((
        f'{{% block {block_id} %}}',
        block,
        f'{{% endblock %}} {{# {block_id} #}}',
    )), 1)

    # Iterate over any children to this toc_token and process them.
    for ix, child in enumerate(toc_token['children']):
        try:
            next_child = toc_token['children'][ix + 1]
        except IndexError:
            next_child = None
        content = _add_block(content, child, next_toc_token=next_child)

    # Done; return the content with blocks.
    return content


def _fmt(src: str, lang: str, css_class: str, *args, **kwargs):
    """Custom Markdown formatter that retains language classes."""
    highlighter = pymdownx.highlight.Highlight(guess_lang=False)
    return highlighter.highlight(src, lang, f'{css_class} language-{lang}')


# Define the superfences extension.
# We need a custom fence to maintain useful language-specific CSS classes.
_superfences = pymdownx.superfences.SuperFencesCodeExtension(
    custom_fences=[{
        'name': '*',
        'class': 'highlight',
        'format': _fmt,
    }],
)
