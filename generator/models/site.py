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
import re
import typing
import uuid

import yaml

from generator import md
from generator.env import jinja_env
from generator.models.aip import AIP
from generator.models.page import Page
from generator.models.scope import Scope
from generator.utils import cached_property


@dataclasses.dataclass(frozen=True)
class Site:
    base_dir: str
    revision: str
    config: typing.Dict[str, typing.Any]

    @classmethod
    def load(cls, base_dir: str) -> Site:
        # Load all site configuration.
        config: typing.Dict[str, typing.Any] = {}
        config_dir = os.path.join(base_dir, 'config')
        for fn in os.listdir(config_dir):
            with io.open(os.path.join(config_dir, fn), 'r') as f:
                config[fn[:-5]] = yaml.safe_load(f)

        # Return a new Site object.
        return cls(
            base_dir=base_dir,
            config=config,
            revision=str(uuid.uuid4())[-8:],
        )

    @cached_property
    def aips(self) -> typing.Dict[int, AIP]:
        """Return all the AIPs in the site."""
        answer = collections.OrderedDict()
        for scope in self.scopes.values():
            for id, aip in scope.aips.items():
                answer[id] = aip
        return answer

    @property
    def base_url(self) -> str:
        """Return the site's base URL."""
        return self.config.get('urls', {}).get('site', '').rstrip('/')

    @property
    def pages(self) -> typing.Dict[str, Page]:
        """Return all of the static pages in the site."""
        # The CONTRIBUTING.md file is a special case: we need it in the
        # root so GitHub will find it.
        answer = {'contributing': self._load_page(
            os.path.join(self.base_dir, 'CONTRIBUTING.md'),
        )}

        # Iterate over the pages directory and load static pages.
        page_dir = os.path.join(self.base_dir, 'pages')
        for fn in os.listdir(page_dir):
            # Sanity check: Ignore non-Markdown files.
            if not fn.endswith(('.md', '.md.j2')):
                continue

            # Load the page and add it to the pages dictionary.
            page = self._load_page(os.path.join(page_dir, fn))
            answer[page.code] = page
        return answer

    @property
    def relative_uri(self) -> str:
        return '/{}'.format('/'.join(self.base_url.split('/')[3:])).rstrip('/')

    @property
    def repo_url(self) -> str:
        return self.config.get('urls', {}).get('repo', '').rstrip('/')

    @property
    def scopes(self) -> typing.Dict[str, Scope]:
        """Return all of the AIP scopes present in the site."""
        answer_list = []
        aip_dir = os.path.join(self.base_dir, 'aip')
        for fn in os.listdir(aip_dir):
            # If there is a scope.yaml file, then this is a scope directory
            # and we add it to our list.
            scope_file = os.path.join(aip_dir, fn, 'scope.yaml')
            if not os.path.exists(scope_file):
                continue

            # Open the scope's configuration file and create a Scope
            # object based on it.
            with io.open(scope_file, 'r') as f:
                conf = yaml.safe_load(f)
            code = conf.pop('code', fn)
            scope = Scope(
                base_dir=os.path.join(aip_dir, fn),
                code=code,
                config=conf,
                order=conf.pop('order', float('inf')),
                site=self,
                title=conf.pop('title', code.capitalize()),
            )

            # Append the scope to our list.
            answer_list.append(scope)

        # Create an ordered dictionary of scopes.
        answer = collections.OrderedDict()
        for scope in sorted(answer_list, key=lambda i: i.order):
            answer[scope.code] = scope
        return answer

    def _load_page(self, md_file: str) -> Page:
        """Load a support page and return a new Page object."""
        # Read the page file from disk.
        with io.open(md_file, 'r') as f:
            content = f.read()

        # If the path is a Jinja template, resolve the content.
        # Only the site is sent as context in this case.
        if md_file.endswith('.j2'):
            content = jinja_env.from_string(content).render(site=self)

        # Check for a config file. If one exists, load it too.
        config_file = re.sub(r'\.md(\.j2)?$', '.yaml', md_file)
        config = {}
        if os.path.exists(config_file):
            with io.open(config_file, 'r') as f:
                config = yaml.safe_load(f.read())

        # Return the page.
        return Page(
            config=config,
            content=md.MarkdownDocument(content),
            repo_path=md_file[len(self.base_dir):],
            site=self,
        )
