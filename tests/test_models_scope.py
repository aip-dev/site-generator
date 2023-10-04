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


def test_aeps(site):
    general = site.scopes['general']
    poetry = site.scopes['poetry']
    assert all([i.id < 1000 for i in general.aeps.values()])
    assert all([i.id > 1000 for i in poetry.aeps.values()])
    assert all([isinstance(i, AEP) for i in general.aeps.values()])


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
    rendered_poetry = site.scopes['poetry'].render()
    assert '<h3 id="hugo">Victor Hugo</h3>' in rendered
    assert '<h3 id="dickens">Dickens</h3>' in rendered
    assert '<h3 id="poetry">Shakespearean Poetry</h3>' in rendered_poetry
