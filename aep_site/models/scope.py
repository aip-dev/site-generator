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

from __future__ import annotations
import collections
import dataclasses
import io
import os
import typing

import yaml

from aep_site.jinja.env import jinja_env
from aep_site.models.aep import AEP
from aep_site.models.aep import Change
from aep_site.utils import cached_property


@dataclasses.dataclass(frozen=True)
class Scope:
    base_dir: str
    code: str
    title: str
    order: int
    site: Site
    config: typing.Dict[str, typing.Any]

    @cached_property
    def aeps(self) -> typing.Dict[int, AEP]:
        """Return a dict of AEPs, sorted by number."""
        answer = []

        # Load each AEP under this scope.
        # Similar to scopes, AEPs are detected based solely on
        # presence of file on disk.
        for fn in os.listdir(self.base_dir):
            path = os.path.join(self.base_dir, fn)
            aep_config = os.path.join(path, 'aep.yaml')
            if os.path.isdir(path) and os.path.exists(aep_config):
                with io.open(aep_config, 'r') as f:
                    meta = yaml.safe_load(f)

            # Sanity check: Does this look like an old-style AEP?
            elif path.endswith('.md'):
                # Load the AEP.
                with io.open(path, 'r') as f:
                    contents = f.read()

                # Parse out the front matter from the Markdown content.
                fm, body = contents.lstrip('-\n').split('---\n', maxsplit=1)
                meta = yaml.safe_load(fm)

            # This is not a recognized AEP.
            else:
                meta = None  # Not needed; fixes a coverage bug.
                continue

            # Create the AEP object.
            answer.append(AEP(
                id=meta.pop('id'),
                config=meta,
                changelog={Change(**i) for i in meta.pop('changelog', [])},
                created=meta.pop('created'),
                path=path,
                scope=self,
                state=meta.pop('state'),
            ))

        answer = sorted(answer, key=lambda i: i.id)
        return collections.OrderedDict([(i.id, i) for i in answer])

    @cached_property
    def categories(self) -> typing.Dict[str, Category]:
        # There may be no categories. This is fine; just "fake" a single
        # category based on the scope.
        #
        # This is guaranteed to have all AEPs, so just return immediately
        # and skip remaining processing.
        if not self.config.get('categories', None):
            return {self.code: Category(
                code=self.code,
                title=self.title,
                order=0,
                aeps=self.aeps,
            )}

        # Iterate over each category and piece together the AEPs in order.
        cats = collections.OrderedDict()
        for ix, cat in enumerate(self.config['categories']):
            # Determine what AEPs are in this category.
            aeps: typing.List[AEP] = []
            for aep in self.aeps.values():
                if aep.placement.category != cat['code']:
                    continue
                aeps.append(aep)
            aeps = sorted(aeps, key=lambda i: i.placement.order)

            # Create the category object and add it.
            cats[cat['code']] = Category(
                code=cat['code'],
                title=cat.get('title', cat['code'].capitalize()),
                order=ix,
                aeps=collections.OrderedDict([(i.id, i) for i in aeps]),
            )
        return cats

    @property
    def relative_uri(self) -> str:
        return f'/{self.code}'

    def render(self):
        """Render the page for this scope."""
        return jinja_env.get_template('aep-listing.html.j2').render(
            path=self.relative_uri,
            scope=self,
            site=self.site,
        )


@dataclasses.dataclass(frozen=True)
class Category:
    code: str
    title: str
    order: int
    aeps: typing.Dict[int, AEP]


if typing.TYPE_CHECKING:
    from aep_site.models.site import Site
