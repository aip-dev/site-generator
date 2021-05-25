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


def test_collections(site):
    assert 'general' in site.collections
    assert 'authors' in site.collections
    assert 'red-herring' not in site.collections
    assert 'dickens' not in site.collections['general'].pages
    assert 'faq' not in site.collections['authors'].pages


def test_code(site):
    assert site.pages['contributing'].code == 'contributing'
    assert site.pages['faq'].code == 'faq'


def test_content(site):
    assert '- Blue\n' in site.pages['faq'].content
    assert '- Yellow\n' in site.pages['faq'].content
    assert '{% for' not in site.pages['faq'].content


def test_relative_uri(site):
    assert site.pages['contributing'].relative_uri == '/contributing'
    assert site.pages['faq'].relative_uri == '/faq'
    assert site.pages['authors/dickens'].relative_uri == '/authors/dickens'


def test_repo_path(site):
    assert site.pages['contributing'].repo_path == '/CONTRIBUTING.md'
    assert site.pages['faq'].repo_path == '/pages/general/faq.md.j2'
    assert site.pages['licensing'].repo_path == '/pages/general/licensing.md'
    assert site.pages['authors/hugo'].repo_path == '/pages/authors/hugo.md'


def test_render(site):
    rendered = site.pages['page'].render()
    assert '<h1 id="this-is-a-page">This is a page.</h1>' in rendered
    assert '<p>Is it not amazing?</p>' in rendered
    assert '<h2 id="information">Information</h2>' in rendered
    assert '<h3 id="fake-latin">Fake Latin</h3>' in rendered
    assert '<h3 id="real-latin">Real Latin</h3>' in rendered


def test_render_special_footer(site):
    rendered = site.pages['licensing'].render()
    assert 'This page was adapted' in rendered


def test_title(site):
    assert site.pages['contributing'].title == 'Contributing'
    assert site.pages['licensing'].title == 'Content licensing'
