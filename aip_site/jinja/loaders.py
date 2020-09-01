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

import io
import os
import re
import typing

import jinja2
import jinja2.loaders

from aip_site.md import MarkdownDocument

if typing.TYPE_CHECKING:
    from aip_site.models.aip import AIP


class AIPLoader(jinja2.loaders.BaseLoader):
    """Loader for loading AIPs."""

    def __init__(self, aip: 'AIP'):
        super().__init__()
        self.aip = aip

    def get_source(self, env, template: str) -> typing.Tuple[str, str, None]:
        # Find the appropriate AIP file.
        if template == 'generic':
            fn = os.path.join(self.aip.path, 'aip.md')
        else:
            view = template.split('.')
            while view:
                view_str = '.'.join(view)
                fn = os.path.join(self.aip.path, f'aip.{view_str}.md')
                if os.path.isfile(fn) or os.path.isfile(f'{fn}.j2'):
                    break
                view = view[1:]

        # Sanity check: Does the file exist?
        # If not, raise an error.
        if not os.path.isfile(fn) and not os.path.isfile(f'{fn}.j2'):
            raise jinja2.TemplateNotFound(
                f'Could not find {template} template for AIP-{self.aip.id}.',
            )

        # Are we loading a plain file or a Jinja2 template file?
        if os.path.isfile(f'{fn}.j2'):
            fn += '.j2'

        # Load the contents.
        with io.open(fn) as f:
            contents = f.read()

        # Add custom {% block %} tags corresponding to Markdown headings.
        #
        # Note: We only do this if the template does not already have
        # {% block %} tags to avoid either stomping over input, or creating
        # an invalid template.
        if not re.search(r'\{%-? block', contents):
            # Iterate over the individual components in the table
            # of contents and make each into a block.
            contents = MarkdownDocument(contents).blocked_content

        # Return the template information.
        return contents, fn, None

    def list_templates(self) -> typing.Sequence[str]:
        answer = []

        # We sort the files in the directory to read more specific
        # files first.
        exts_regex = r'(\.(j2|md|proto|oas|yaml))*$'
        for fn in sorted(os.listdir(self.aip.path),
                key=lambda p: len(re.sub(exts_regex, '', p).split('.')),
                reverse=True):

            # Each file may specify a view, which corresponds to a separate
            # template.
            view = '.'.join(re.sub(exts_regex, '', fn).split('.')[1:])
            if view and view not in answer:
                answer.append(view)

        # There is always a generic view.
        answer.append('generic')
        return answer
