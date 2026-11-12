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
import tempfile

from aip_site.publisher import Publisher


SEARCH_JS = os.path.join(
    os.path.dirname(__file__), '..',
    'aip_site', 'support', 'assets', 'js', 'search', 'search.js',
)


def test_publisher():
    with tempfile.TemporaryDirectory() as tmp:
        pub = Publisher('tests/test_data/', tmp)
        pub.publish_site()


def test_publisher_search_assets():
    with tempfile.TemporaryDirectory() as tmp:
        Publisher('tests/test_data/', tmp).publish_site()
        search_dir = os.path.join(tmp, 'assets', 'js', 'search')
        assert os.path.isfile(os.path.join(search_dir, 'search.js'))
        assert os.path.isfile(
            os.path.join(search_dir, 'tipuesearch_content.js'),
        )
        assert not os.path.exists(
            os.path.join(search_dir, 'tipuesearch.min.js'),
        )
        with io.open(os.path.join(tmp, 'search.html'), 'r') as f:
            html = f.read()
        assert '/assets/js/search/search.js' in html
        assert 'tipuesearch.min.js' not in html


def test_search_js_uses_text_only_dom_apis():
    """Lint search.js for HTML-parsing and dynamic-code APIs.

    search.js is expected to build results with text-only DOM APIs and plain
    string matching. This is a tripwire, not a proof.
    """
    with io.open(SEARCH_JS, 'r') as f:
        code = '\n'.join(
            line for line in f.read().splitlines()
            if not line.lstrip().startswith('//')
        )
    for pattern in (
        r'innerHTML', r'outerHTML', r'insertAdjacentHTML',
        r'document\.write', r'\.html\(', r'\bRegExp\b', r'\beval\b',
        r'new Function', r'createContextualFragment', r'DOMParser',
        r'srcdoc', r'\$\(', r'jQuery',
    ):
        assert not re.search(pattern, code), pattern
