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
import datetime
import io
import typing

import yaml

from generator import md
from generator.env import jinja_env


@dataclasses.dataclass(frozen=True)
class AIP:
    id: int
    state: str
    created: datetime.date
    scope: Scope
    body: str
    repo_path: str
    config: typing.Dict[str, typing.Any]
    changelog: typing.Set[Change] = dataclasses.field(default_factory=set)

    @property
    def content(self) -> md.MarkdownDocument:
        if not hasattr(self, '_md_content'):
            answer = self.body
            if self.changelog:
                answer += '\n\n## Changelog\n\n'
                for cl in sorted(self.changelog):
                    answer += f'- **{cl.date}:** {cl.message}\n'
            self._md_content = md.MarkdownDocument(answer)
        return self._md_content

    @property
    def placement(self) -> Placement:
        """Return the placement data for this AIP, or sensible defaults."""
        return Placement(**self.config.get('placement', {}))

    @property
    def redirects(self) -> typing.Set[str]:
        uris = {f'/{self.id:04d}', f'/{self.id:03d}', f'/{self.id:02d}'}
        uris = uris.difference({self.relative_uri})
        if 'redirect_from' in self.config:
            uris.add(self.config['redirect_from'])
        return uris

    @property
    def relative_uri(self) -> str:
        """Return the relative URI for this AIP."""
        if self.scope != 'general':
            return f'/{self.scope}/{self.id}'
        return f'/{self.id}'

    @property
    def site(self) -> Site:
        """Return the site for this AIP."""
        return self.scope.site

    @property
    def title(self) -> str:
        """Return the AIP title."""
        return self.content.title

    @property
    def updated(self):
        """Return the most recent date on the changelog.

        If there is no changelog, return the created date instead.
        """
        if self.changelog:
            return sorted(self.changelog)[0].date
        return self.created

    def render(self):
        """Return the fully-rendered page for this AIP."""
        return jinja_env.get_template('aip.html.j2').render(
            aip=self,
            path=self.relative_uri,
            site=self.site,
        )

    def _injest_changelog(self, filename: str):
        """Injest a fragment of an AIP changelog into the object."""
        with io.open(filename, 'r') as f:
            conf = yaml.safe_load(f)
        for cl in conf.get('changelog', ()):
            self.changelog.add(Change(**cl))


@dataclasses.dataclass
class Change:
    date: datetime.date
    message: str

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other: 'Change'):
        # We sort changes in reverse-cron, so a later date is "less" here.
        return self.date > other.date

    def __str__(self):
        return f'{self.date.isoformat()}: {self.message}'


@dataclasses.dataclass(frozen=True)
class Placement:
    category: str = 'misc'
    order: typing.Union[int, float] = float('inf')


if typing.TYPE_CHECKING:
    from generator.models.scope import Scope
    from generator.models.site import Site
