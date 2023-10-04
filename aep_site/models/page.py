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
import dataclasses
import io
import re
import os
import typing

import yaml

from aip_site import md
from aip_site.jinja.env import jinja_env
from aip_site.utils import cached_property


@dataclasses.dataclass(frozen=True)
class Page:
    body: md.MarkdownDocument
    repo_path: str
    collection: Collection
    config: typing.Dict[str, typing.Any]

    @property
    def code(self) -> str:
        """Return this page's code.

        Note: Uniqueness is only guaranteed within the collection.
        """
        return self.repo_path.split('/')[-1].split('.')[0].lower()

    @cached_property
    def content(self) -> md.MarkdownDocument:
        """Return the Markdown content for this page."""
        # If this was originally a Jinja template, then we need to render
        # this specific content in isolation (apart from the page template).
        if self.repo_path.endswith('.j2'):
            return md.MarkdownDocument(
                jinja_env.from_string(self.body).render(site=self.site),
            )

        # This is not a template; just return the body directly.
        return self.body

    @property
    def relative_uri(self) -> str:
        return f'/{self.collection.code}/{self.code}'.replace('/general', '')

    @property
    def site(self) -> Site:
        return self.collection.site

    @property
    def title(self) -> str:
        """Return the page title."""
        return self.content.title

    def render(self) -> str:
        return jinja_env.get_template('page.html.j2').render(
            page=self,
            path=self.relative_uri,
            site=self.site,
        )


@dataclasses.dataclass(frozen=True)
class Collection:
    code: str
    site: Site

    @property
    def base_dir(self) -> str:
        return os.path.join(self.site.base_dir, 'pages', self.code)

    @cached_property
    def pages(self) -> typing.Dict[str, Page]:
        """Return the pages in this collection."""
        answer = {}

        # For the general collection, the CONTRIBUTING.md file is a special
        # case: we need it in the root so GitHub will find it.
        if self.code == 'general':
            answer['contributing'] = self._load_page(
                os.path.join(self.site.base_dir, 'CONTRIBUTING.md'),
            )

        # Iterate over the pages directory and load static pages.
        for fn in os.listdir(self.base_dir):
            # Sanity check: Ignore non-Markdown files.
            if not fn.endswith(('.md', '.md.j2')):
                continue

            # Load the page and add it to the pages dictionary.
            page = self._load_page(os.path.join(self.base_dir, fn))
            answer[page.code] = page
        return answer

    def _load_page(self, md_file: str) -> Page:
        """Load a support page and return a new Page object."""
        # Read the page file from disk.
        with io.open(md_file, 'r') as f:
            body = f.read()

        # Check for a config file. If one exists, load it too.
        config_file = re.sub(r'\.md(\.j2)?$', '.yaml', md_file)
        config = {}
        if os.path.exists(config_file):
            with io.open(config_file, 'r') as f:
                config = yaml.safe_load(f)

        # Return the page.
        return Page(
            body=md.MarkdownDocument(body),
            collection=self,
            config=config,
            repo_path=md_file[len(self.site.base_dir):],
        )


if typing.TYPE_CHECKING:
    from aip_site.models.site import Site
