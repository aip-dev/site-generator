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

import jinja2
import pytest


def test_list_templates(site):
    assert site.aeps[62].env.list_templates() == ['en', 'generic']
    assert site.aeps[38].env.list_templates() == ['generic']


def test_get_template(site):
    assert isinstance(
        site.aeps[62].env.get_template('generic'),
        jinja2.Template,
    )
    with pytest.raises(jinja2.TemplateNotFound):
        site.aeps[62].env.get_template('bogus')


def test_template_auto_blocks(site):
    generic = site.aeps[62].env.get_template('generic')
    assert tuple(generic.blocks.keys()) == (
        'guidance',
        'bp_myriel',
        'interface_definitions',
        'reading_a_book',
        'further_reading',
    )
