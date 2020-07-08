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
import io
import os
import re
import shutil
import sys
import typing

from scss.compiler import compile_file  # type: ignore

from generator import env
from generator.models.aip import AIP
from generator.models.scope import Scope
from generator.models.site import Site
from generator.models.page import Page


GENERATOR_ROOT = os.path.realpath(
    os.path.join(os.path.dirname(__file__), '..'),
)


class Publisher:
    """Class for writing the AIP site out to disk."""

    def __init__(self, src, dest, *, log_to_stdout=False):
        self.output_dir = dest.rstrip(os.path.sep)
        self.log_to_stdout = log_to_stdout
        self.site = Site.load(src.rstrip(os.path.sep))

    def log(self, message: str, *, err: bool = False):
        """Conditionally log a message."""
        dest = sys.stderr if err else sys.stdout
        if self.log_to_stdout:
            print(f'{message}', file=dest)

    def publish_site(self):
        """Publish the full site."""
        # Publish every page, AIP listing, and AIP.
        for page in self.site.pages.values():
            self.publish_doc(page)
        for scope in self.site.scopes.values():
            self.publish_doc(scope)
        for aip in self.site.aips.values():
            self.publish_doc(aip)

        # Publish support pages that are not Markdown pages.
        self.publish_template('index.html.j2', 'index.html')
        self.publish_template('search.html.j2', 'search.html')

        # Copy over static files verbatim.
        self.publish_static()

        # Publish dynamic content that goes in the static directory.
        self.publish_template(
            'search.js.j2',
            'static/js/search/tipuesearch_content.js',
        )
        self.publish_css()

    def publish_doc(self, doc: typing.Union[AIP, Scope, Page]):
        """Publish a single AIP document to disk."""
        # Determine the path and make sure the directory exists.
        path = f'{self.output_dir}{doc.relative_uri}.html'
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Write the document's file to disk.
        with io.open(path, 'w') as f:
            f.write(doc.render())
        self.log(f'Successfully wrote {path}.')

        # If this document has any redirects (only AIPs do as of this writing),
        # write out the redirect files to disk also.
        for redirect in getattr(doc, 'redirects', set()):
            rpath = f'{self.output_dir}{redirect}.html'
            with io.open(rpath, 'w') as f:
                f.write(env.jinja_env.get_template('redirect.html.j2').render(
                    site=self.site,
                    target=doc,
                ))
            self.log(f'Successfully wrote {rpath} (redirect).')

    def publish_template(self, tmpl: str, path: str):
        """Publish a site-wide template to a particular path."""
        path = f'{self.output_dir}{os.path.sep}{path}'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, 'w') as f:
            f.write(env.jinja_env.get_template(tmpl).render(
                site=self.site,
                path=path.split('.')[0],
            ))
        self.log(f'Successfully wrote {path}.')

    def publish_static(self):
        """Copy the static directory."""
        shutil.copytree(
            src=os.path.join(GENERATOR_ROOT, 'static'),
            dst=os.path.join(self.output_dir, 'static'),
            dirs_exist_ok=True,
        )
        self.log('Successfully wrote static files.')

    def publish_css(self):
        """Compile and publish all SCSS files in the root SCSS directory."""
        scss_path = os.path.join(GENERATOR_ROOT, 'scss')
        css_path = os.path.join(self.output_dir, 'static', 'css')
        os.makedirs(css_path, exist_ok=True)
        for scss_file in os.listdir(scss_path):
            if not scss_file.endswith('.scss'):
                continue
            css_file = os.path.join(
                css_path,
                re.sub(r'\.scss$', '.css', scss_file),
            )
            with io.open(css_file, 'w') as f:
                f.write(compile_file(os.path.join(scss_path, scss_file)))
            self.log(f'Successfully wrote {css_file}.')
