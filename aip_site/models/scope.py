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

from aip_site.jinja.env import jinja_env
from aip_site.models.aip import AIP
from aip_site.models.aip import Change
from aip_site.utils import cached_property


@dataclasses.dataclass(frozen=True)
class Scope:
    base_dir: str
    code: str
    title: str
    order: int
    site: Site
    config: typing.Dict[str, typing.Any]

    @cached_property
    def aips(self) -> typing.Dict[int, AIP]:
        """Return a dict of AIPs, sorted by number."""
        answer = []

        # Load each AIP under this scope.
        # Similar to scopes, AIPs are detected based solely on
        # presence of file on disk.
        for fn in os.listdir(self.base_dir):
            path = os.path.join(self.base_dir, fn)
            aip_config = os.path.join(path, 'aip.yaml')
            if os.path.isdir(path) and os.path.exists(aip_config):
                with io.open(aip_config, 'r') as f:
                    meta = yaml.safe_load(f)

            # Sanity check: Does this look like an old-style AIP?
            elif path.endswith('.md'):
                # Load the AIP.
                with io.open(path, 'r') as f:
                    contents = f.read()

                # Parse out the front matter from the Markdown content.
                fm, body = contents.lstrip('-\n').split('---\n', maxsplit=1)
                meta = yaml.safe_load(fm)

            # This is not a recognized AIP.
            else:
                meta = None  # Not needed; fixes a coverage bug.
                continue

            # Create the AIP object.
            answer.append(AIP(
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
        # This is guaranteed to have all AIPs, so just return immediately
        # and skip remaining processing.
        if not self.config.get('categories', None):
            return {self.code: Category(
                code=self.code,
                title=self.title,
                order=0,
                aips=self.aips,
            )}

        # Iterate over each category and piece together the AIPs in order.
        cats = collections.OrderedDict()
        for ix, cat in enumerate(self.config['categories']):
            # Determine what AIPs are in this category.
            aips: typing.List[AIP] = []
            for aip in self.aips.values():
                if aip.placement.category != cat['code']:
                    continue
                aips.append(aip)
            aips = sorted(aips, key=lambda i: i.placement.order)

            # Create the category object and add it.
            cats[cat['code']] = Category(
                code=cat['code'],
                title=cat.get('title', cat['code'].capitalize()),
                order=ix,
                aips=collections.OrderedDict([(i.id, i) for i in aips]),
            )
        return cats

    @property
    def relative_uri(self) -> str:
        return f'/{self.code}'

    def render(self):
        """Render the page for this scope."""
        return jinja_env.get_template('aip-listing.html.j2').render(
            path=self.relative_uri,
            scope=self,
            site=self.site,
        )


@dataclasses.dataclass(frozen=True)
class Category:
    code: str
    title: str
    order: int
    aips: typing.Dict[int, AIP]


if typing.TYPE_CHECKING:
    from aip_site.models.site import Site
