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
import uuid

import yaml

from aip_site.models.aip import AIP
from aip_site.models.page import Collection
from aip_site.models.page import Page
from aip_site.models.scope import Scope
from aip_site.utils import cached_property


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

    @cached_property
    def collections(self) -> typing.Dict[str, Collection]:
        """Return all of the page collections in the site."""
        pages_dir = os.path.join(self.base_dir, 'pages')
        answer = {}
        for dirname in os.listdir(pages_dir):
            # Sanity check: Is this a directory?
            if not os.path.isdir(os.path.join(pages_dir, dirname)):
                continue
            answer[dirname] = Collection(code=dirname, site=self)
        return answer

    @property
    def pages(self) -> typing.Dict[str, Page]:
        """Return all of the static pages in the site."""
        answer = {}
        for col in self.collections.values():
            for page in col.pages.values():
                # Disambiguate the pages from one another, but treat the
                # general collection as special and remove the prefix.
                code = f'{col.code}/{page.code}'.replace('general/', '')
                answer[code] = page
        return answer

    @property
    def relative_uri(self) -> str:
        return '/{}'.format('/'.join(self.base_url.split('/')[3:])).rstrip('/')

    @property
    def repo_url(self) -> str:
        return self.config.get('urls', {}).get('repo', '').rstrip('/')

    @cached_property
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
