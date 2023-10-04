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

from aep_site.models.aep import AEP
from aep_site.models.page import Page
from aep_site.models.scope import Scope


def test_aeps(site):
    assert isinstance(site.aeps, dict)
    assert all([isinstance(i, AEP) for i in site.aeps.values()])
    assert 62 in site.aeps
    assert 1622 in site.aeps


def test_base_url(site):
    assert site.base_url == 'https://aep.dev'


def test_pages(site):
    assert isinstance(site.pages, dict)
    assert all([isinstance(i, Page) for i in site.pages.values()])
    assert 'licensing' in site.pages
    assert 'contributing' in site.pages


def test_relative_uri(site):
    assert site.relative_uri == ''
    site.config['urls']['site'] = 'https://foo.github.io/bar/'
    assert site.relative_uri == '/bar'


def test_repo_url(site):
    assert site.repo_url == 'https://github.com/aep-dev/site-generator'


def test_scopes(site):
    assert isinstance(site.scopes, dict)
    assert all([isinstance(i, Scope) for i in site.scopes.values()])
    assert 'general' in site.scopes
    assert 'poetry' in site.scopes
    assert 'red-herring' not in site.scopes
