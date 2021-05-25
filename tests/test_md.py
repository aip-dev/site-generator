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

import pytest

from aip_site import md


@pytest.fixture
def markdown_doc():
    return md.MarkdownDocument(textwrap.dedent("""
        # Title

        This is an intro paragraph.

        ## Sub 1

        Stuff and things, things and stuff.

        ### Drilling down

        This had a deeper item.

        ```python
        # This is a code example.
        ```

        ### Still drilling

        Drill drill drill

        ## Sub 2

        Weeeee
    """).strip())


def test_blocked_content(markdown_doc):
    blocked = markdown_doc.blocked_content
    blocks = ('sub_1', 'drilling_down', 'still_drilling', 'sub_2')
    for ix, block in enumerate(blocks):
        assert f'{{% block {block} %}}' in blocked
        assert f'{{% endblock %}} {{# {block} #}}' in blocked

    # Also ensure that the blocks both open and close in the correct order.
    now_or_later = (
        ('{% block sub_1 %}', '{% block drilling_down %}'),
        ('{% block sub_1 %}', '{% block still_drilling %}'),
        ('{% block sub_1 %}', '{% block sub_2 %}'),
        ('{% endblock %} {# drilling_down #}', '{% block still_drilling %}'),
        ('{% endblock %} {# drilling_down #}', '{% endblock %} {# sub_1 #}'),
        ('{% endblock %} {# still_drilling #}', '{% endblock %} {# sub_1 #}'),
        ('{% endblock %} {# sub_1 #}', '{% endblock %} {# sub_2 #}'),
    )
    for now, later in now_or_later:
        assert blocked.index(now) < blocked.index(later)


def test_blocked_content_error_boundaries(markdown_doc):
    # Maliciously screw up the toc since I do not actually know how
    # to trigger these error cases otherwise.
    markdown_doc.html
    markdown_doc._engine.toc_tokens.append({
        'level': 2,
        'id': 'missing',
        'name': 'Missing',
        'children': [],
    })

    # Some blocks would actually be added in this situation, but this is
    # undefined behavior. We just test that we get content back.
    assert isinstance(markdown_doc.blocked_content, str)
    assert '### Drilling down' in markdown_doc.blocked_content


def test_coerce(markdown_doc):
    assert '# Title' in markdown_doc
    assert '# Title' in str(markdown_doc)


def test_html(markdown_doc):
    assert '<h1 id="title">Title</h1>' in markdown_doc.html
    assert '<h2 id="sub-1">Sub 1</h2>' in markdown_doc.html
    assert '<h3 id="still-drilling">Still drilling</h3>' in markdown_doc.html
    assert '<p>Stuff and things, things and stuff.</p>' in markdown_doc.html
    assert '<div class="highlight language-python">' in markdown_doc.html
    assert markdown_doc.html is markdown_doc.html


def test_title(markdown_doc):
    assert markdown_doc.title == 'Title'


def test_toc(markdown_doc):
    assert 'Sub 1' in markdown_doc.toc
    assert 'Drilling down' in markdown_doc.toc
    assert 'Still drilling' in markdown_doc.toc
    assert 'Sub 2' in markdown_doc.toc
    assert 'Title' not in markdown_doc.toc  # Note: not in.
    assert 'Stuff and things' not in markdown_doc.toc
