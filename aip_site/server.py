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

import os
import re

from scss.compiler import compile_file  # type: ignore
import flask

from aip_site.jinja.env import jinja_env
from aip_site.models.site import Site


ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
app = flask.Flask('aip', static_folder=f'{ROOT}/aip_site/support/assets/')
app.jinja_env = jinja_env  # type: ignore


@app.route('/')
def hello():
    return flask.render_template('index.html.j2', site=flask.g.site)


@app.route('/<int:aip_id>')
def aip(aip_id: int):
    """Display a single AIP document."""
    return flask.g.site.aips[aip_id].render()


@app.route('/search')
def search():
    """Display the search page."""
    return flask.render_template('search.html.j2',
        site=flask.g.site,
        path=flask.request.path,
    )


@app.route('/<page>')
@app.route('/<collection>/<page>')
def page(page: str, collection: str = 'general'):
    """Display a static page or listing of AIPs in a given scope."""
    site = flask.g.site
    if page in site.scopes:
        return site.scopes[page].render()
    return site.collections[collection].pages[page].render()


@app.route('/assets/css/<path:css_file>')
def scss(css_file: str):
    """Compile the given SCSS file and return it."""
    scss_file = re.sub(r'\.css$', '.scss', css_file)
    css = compile_file(f'{ROOT}/aip_site/support/scss/{scss_file}')
    return flask.Response(css, mimetype='text/css')


@app.route('/assets/js/search/tipuesearch_content.js')
def search_content():
    """Compile the search content JavaScript and return it."""
    return flask.Response(
        flask.render_template('search.js.j2', site=flask.g.site),
        mimetype='text/javascript',
    )


def site_load_func(src: str):
    """Return a function that loads the site and registers it.

    This is used in cli.py to register to Flask.before_request.
    """
    def fx():
        flask.g.site = Site.load(src)

        # This is the dev server, so plow over whatever the configuration
        # says that the site URL is.
        flask.g.site.config.setdefault('urls', {})
        flask.g.site.config['urls']['site'] = 'http://localhost:4000'
    return fx
