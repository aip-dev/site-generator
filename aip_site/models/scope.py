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

import jinja2
import yaml

from aip_site.jinja.env import jinja_env
from aip_site.md import MarkdownDocument
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
            templates = collections.OrderedDict()

            # If this is an AIP directory, parse all the files inside it.
            aip_config = os.path.join(path, 'aip.yaml')
            if os.path.isdir(path) and os.path.exists(aip_config):
                with io.open(aip_config, 'r') as f:
                    meta = yaml.safe_load(f)

                # We sort the files in the directory to read more specific
                # files first.
                for sfn in sorted(os.listdir(path),
                        key=lambda p: len(p.rstrip('.j2').split('.')),
                        reverse=True):
                    # Sanity check: Is this an AIP content file?
                    if not sfn.endswith(('.md', '.md.j2')):
                        continue

                    # Load the contents.
                    with io.open(os.path.join(path, sfn)) as f:
                        contents = f.read()

                    # Transform the contents into a template if it is not
                    # already.
                    #
                    # We do this by adding {% block %} tags corresponding to
                    # Markdown headings.
                    if not sfn.endswith('.j2'):
                        # Iterate over the individual components in the table
                        # of contents and make each into a block.
                        contents = MarkdownDocument(contents).blocked_content

                    # Get the view from the filename.
                    while sfn.endswith(('.md', '.j2')):
                        sfn = sfn[:-3]
                    try:
                        view = sfn.split('.')[1:][0]
                    except IndexError:
                        view = 'generic'

                    # Create a template object for the contents.
                    contents_tmpl = jinja2.Template(contents,
                        extensions=jinja_env.extensions,
                        undefined=jinja2.StrictUndefined,
                    )
                    contents_tmpl.filename = path

                    # Add the template to the set of templates.
                    templates[view] = contents_tmpl

            # Sanity check: Does this look like an old-style AIP?
            elif fn.endswith('.md'):
                # Load the AIP.
                with io.open(path, 'r') as f:
                    contents = f.read()

                # Parse out the front matter from the Markdown content.
                fm, body = contents.lstrip('-\n').split('---\n', maxsplit=1)
                templates['generic'] = jinja2.Template(body)
                meta = yaml.safe_load(fm)

            # This is not a recognized AIP.
            else:
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
                templates=templates,
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
