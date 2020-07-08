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
import typing

from generator import md
from generator.env import jinja_env


@dataclasses.dataclass(frozen=True)
class Page:
    code: str
    content: md.MarkdownDocument
    site: Site
    config: typing.Dict[str, typing.Any]

    @property
    def relative_uri(self) -> str:
        return f'/{self.code}'

    @property
    def repo_path(self) -> str:
        if self.code == 'contributing':
            return '/CONTRIBUTING.md'
        return f'/site/pages/{self.code}.md'

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


if typing.TYPE_CHECKING:
    from generator.models.site import Site
