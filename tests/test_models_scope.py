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

from aip_site.models.aip import AIP


def test_aips(site):
    general = site.scopes['general']
    poetry = site.scopes['poetry']
    assert all([i.id < 1000 for i in general.aips.values()])
    assert all([i.id > 1000 for i in poetry.aips.values()])
    assert all([isinstance(i, AIP) for i in general.aips.values()])


def test_categories(site):
    general = site.scopes['general']
    poetry = site.scopes['poetry']
    assert len(general.categories) == 2
    assert 'hugo' in general.categories
    assert 'dickens' in general.categories
    assert len(poetry.categories) == 1
    assert 'poetry' in poetry.categories


def test_relative_uri(site):
    for scope in site.scopes.values():
        assert scope.relative_uri == f'/{scope.code}'


def test_render(site):
    rendered = site.scopes['general'].render()
    assert '<h3>Victor Hugo</h3>' in rendered
    assert '<h3>Dickens</h3>' in rendered
    assert '<h3>Shakespearean Poetry</h3>' in site.scopes['poetry'].render()
