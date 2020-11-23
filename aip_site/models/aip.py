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
import datetime
import io
import re
import typing

import jinja2

from aip_site import md
from aip_site.jinja.env import jinja_env
from aip_site.jinja.ext.sample import SampleExtension
from aip_site.jinja.ext.tab import TabExtension
from aip_site.jinja import loaders
from aip_site.utils import cached_property


@dataclasses.dataclass(frozen=True)
class AIP:
    id: int
    state: str
    created: datetime.date
    scope: Scope
    path: str
    config: typing.Dict[str, typing.Any]
    changelog: typing.Set[Change] = dataclasses.field(default_factory=set)

    @cached_property
    def content(self) -> md.MarkdownDocument:
        # Render the content template into the actual content.
        answer = next(iter(self.templates.values())).render(
            aip=self,
            site=self.site,
        )

        # TEMPORARY: In the interest of having two discrete migrations,
        # rewrite the old link style to the new one.
        answer = re.sub(
            r'\.?\./0([\d]{1,3})\.md',
            lambda m: f'{self.site.relative_uri}/{int(m.groups()[0]):d}',
            answer,
        )

        # Hotlink AIP references.
        # We only hotlink the generally-applicable ones for now until we have
        # a prefix system implemented.
        answer = re.sub(
            r'\b(?<!\[)AIP-([\d]{1,3})\b',  # AIP-###, but not after a `[`.
            fr'[AIP-\1]({self.site.relative_uri}/\1)',
            answer,
        )
        answer = re.sub(
            r'(?<=\])\[aip-([\d]{1,3})\]',  # [aip-###], after a `]`.
            fr'({self.site.relative_uri}/\1)',
            answer,
        )

        # Append the changelog if there is one.
        if self.changelog:
            answer += '\n\n## Changelog\n\n'
            for cl in sorted(self.changelog):
                answer += f'- **{cl.date}:** {cl.message}\n'

        # Return the document.
        return md.MarkdownDocument(answer)

    @cached_property
    def env(self) -> jinja2.Environment:
        return jinja2.Environment(
            extensions=[
                SampleExtension,
                TabExtension,
            ],
            loader=loaders.AIPLoader(self),
            undefined=jinja2.StrictUndefined,
        )

    @property
    def placement(self) -> Placement:
        """Return the placement data for this AIP, or sensible defaults."""
        p = self.config.get('placement', {})
        p.setdefault('category', self.scope.code)
        return Placement(**p)

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
        if self.scope.code != 'general':
            return f'/{self.scope.code}/{self.id}'
        return f'/{self.id}'

    @property
    def repo_path(self) -> str:
        """Return the relative repository path."""
        return self.path[len(self.site.base_dir):]

    @property
    def site(self) -> Site:
        """Return the site for this AIP."""
        return self.scope.site

    @cached_property
    def templates(self) -> typing.Dict[str, jinja2.Template]:
        """Load and return the templates for this AIP."""
        # Sanity check: Is this a legacy AIP (in the old Jekyll format)?
        # If so, process out a single template and return it.
        if self._legacy:
            with io.open(self.path, 'r') as f:
                contents = f.read()
            _, body = contents.lstrip('-\n').split('---\n', maxsplit=1)
            return {'generic': jinja2.Template(body,
                undefined=jinja2.StrictUndefined,
            )}

        # Return a dictionary with all of the templates.
        #
        # Note: This could be made more efficient in the future by only loading
        # the template that the user wants.
        return collections.OrderedDict([
            (k, self.env.get_template(k)) for k in self.env.list_templates()
        ])

    @cached_property
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

    @property
    def _legacy(self) -> bool:
        """Return True if this is a legacy AIP, False otherwise."""
        return self.path.endswith('.md')

    def render(self):
        """Return the fully-rendered page for this AIP."""
        return jinja_env.get_template('aip.html.j2').render(
            aip=self,
            path=self.relative_uri,
            site=self.site,
        )


@dataclasses.dataclass(frozen=True)
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
    category: str
    order: typing.Union[int, float] = float('inf')


if typing.TYPE_CHECKING:
    from aip_site.models.scope import Scope
    from aip_site.models.site import Site
