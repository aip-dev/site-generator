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

from aip_site import md
from aip_site.env import jinja_env
from aip_site.utils import cached_property


@dataclasses.dataclass(frozen=True)
class Page:
    body: md.MarkdownDocument
    repo_path: str
    site: Site
    config: typing.Dict[str, typing.Any]

    @property
    def code(self) -> str:
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
        return f'/{self.code}'

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
    from aip_site.models.site import Site
