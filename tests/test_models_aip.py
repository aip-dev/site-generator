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

from datetime import date

from aip_site.models.aip import Change


def test_content(site):
    # Test with a changelog.
    christmas = site.aips[43]
    assert 'Marley was dead' in christmas.content
    assert '## Changelog' in christmas.content

    # Test without a changelog.
    tale = site.aips[59]
    assert 'It was the best of times' in tale.content
    assert 'Changelog' not in tale.content


def test_content_hotlinking(site):
    hunchback = site.aips[31]
    les_mis = site.aips[62]
    assert '[AIP-62](/62)' in hunchback.content
    assert '[Orpheus](/1622)' in hunchback.content
    assert '[AIP-1609](/1609)' in hunchback.content
    assert '[A Tale of Two Cities](/59)' in hunchback.content
    assert '[AIP-31](/31)' in les_mis.content
    assert '[[AIP-31](/31)](/31)' not in les_mis.content


def test_content_hotlinking_relative_uri(site):
    site.config['urls']['site'] = 'https://github.io/aip'
    hunchback = site.aips[31]
    assert '[AIP-62](/aip/62)' in hunchback.content


def test_placement(site):
    christmas = site.aips[43]
    assert christmas.placement.category == 'dickens'
    assert christmas.placement.order == 10
    sonnet = site.aips[1609]
    assert sonnet.placement.category == 'poetry'
    assert sonnet.placement.order == float('inf')


def test_redirects(site):
    assert site.aips[43].redirects == {'/0043', '/043'}
    assert site.aips[59].redirects == {'/0059', '/059', '/two-cities'}
    assert site.aips[1622].redirects == {'/1622'}


def test_relative_uri(site):
    assert site.aips[43].relative_uri == '/43'
    assert site.aips[1622].relative_uri == '/poetry/1622'


def test_site(site):
    assert all([i.site is site for i in site.aips.values()])


def test_title(site):
    assert site.aips[43].title == 'A Christmas Carol'
    assert site.aips[62].title == 'Les Misérables'


def test_updated(site):
    assert site.aips[62].updated == date(1862, 4, 21)
    assert site.aips[43].updated == date(1844, 12, 25)


def test_views(site):
    les_mis = site.aips[62]
    kw = {'aip': les_mis, 'site': site}
    assert 'Quoique ce' in les_mis.templates['generic'].render(**kw)
    assert 'Quoique ce' not in les_mis.templates['en'].render(**kw)
    assert 'Although' not in les_mis.templates['generic'].render(**kw)
    assert 'Although' in les_mis.templates['en'].render(**kw)
    assert 'Myriel was Bishop' in les_mis.templates['generic'].render(**kw)
    assert 'Myriel was Bishop' in les_mis.templates['en'].render(**kw)


def test_render(site):
    rendered = site.aips[43].render()
    assert '<h1 id="a-christmas-carol">A Christmas Carol</h1>' in rendered
    assert '<h2 id="guidance">Guidance</h2>' in rendered
    assert '<h2 id="changelog">Changelog</h2>' in rendered


def test_change_ordering():
    a = Change(date=date(2020, 4, 21), message='Eight years')
    b = Change(date=date(2012, 4, 21), message='Got married')
    assert a < b
