# aep.dev static site generator

This is the site generator for [aep.dev](https://aep.dev) and its forks. It
takes AEP files in a git repository and outputs a static website.

## Why?

We are not fans of rolling our own tools when off-the-shelf alternatives exist.
However, the AEP project has grown sufficiently mature to warrant it.

GitHub Pages normally automatically builds documentation with [Jekyll][], but
as the AEP system has grown, we are beginning to reach the limits of what
Jekyll can handle, and other off-the-shelf generators had similar issues:

- AEP adoption is handled through fork-and-merge and top-down configuration
  files will lead to repetitive merge conflicts.
- Our grouping and listing logic has grown complicated, and had to be
  maintained using complex and error-prone Liquid templates.
- Jekyll is extensible but GitHub requires specific Jekyll plugins, meaning we
  can not use off-the-shelf solutions for planned features (e.g. tabbed code
  examples).
- Lack of meaningful build CI caused failures.
- Working with the development environment was (really) slow.

There are some additional advantages that we unlock with a custom generator:

- We can override segments of AEPs using template extensions in new files
  rather than modifying existing files.
- We can provide useful abstractions for common deviations between companies
  (e.g. case systems) that minimize the need to fork AEPs.
- We can customize the Markdown parsing where necessary (tabs, hotlinking,
  etc.).

## How does it work?

This is essentially split into three parts:

- Python code (`aep_site/`):
  - The majority of the code is models (`aep_site/models/`) that represent the
    fundamental concept of an AEP site. These are rolled up into a singleton
    object called `Site` that is used everywhere. All models are
    [dataclasses][] that get sent to templates.
  - There is also a publisher class (`aep_site/publisher.py`) that is able to
    slurp up a repo of AEPs and build a static site.
  - There is some server code (`aep_site/server.py`) that can run a development
    server.
  - All remaining files are thin support code to avoid repeating things in or
    between the above.
- Templates (`support/templates/`) are [Jinja2][] templates containing (mostly)
  HTML that makes up the layout of the site.
- Assets (`support/assets/` and `support/scss/`) are other static files. SCSS
  is automatically compiled into CSS at publication.

Of the models, there are three models in particular that matter:

- **Site:** A singleton that provides access to all scopes, AEPs, and static
  pages. This is sent to every template as the `site` variable.
- **AEP:** A representation of a single AEP, including both content and
  metadata. This is sent to the AEP rendering template as the `aep` variable.
- **Scope:** A group of AEPs that apply to a particular scope. The "general"
  scope is special, and is the "root" group. This is sent to the AEP _listing_
  template as the `scope` variable.

Templates are [jinja2][] files in the `templates/` directory.

**Note:** We run Jinja in with "strict undefined", so referencing an undefined
variable in a template is a hard error rather than an empty string.

### Entry points

There are two entry points for the app. The _publisher_
(`aep_site/publisher.py`) is the program that iterates over the relevant
directories, renders HTML files, and writes them out to disk. The _app_
(`aep_site/server.py`) is a lightweight Flask app that provides a development
server.

These entry points are routed through the CLI file (`aep_site/cli.py`); when
this application is installed using pip, it makes the `aep-site-gen`
(publisher) and `aep-site-serve` (server) commands available.

### Extensions

This site generator includes a basic extension system for AEPs. When processing
AEPs as plain Markdown files, it will make any Markdown (level 2 or 3) header
into a block. Therefore...

```md
## Foo bar baz

Lorem ipsum dolor set amet
```

Becomes...

```j2
{% block foo_bar_baz %}
## Foo bar baz

Lorem ipsum dolor set amet
{% endblock %}
```

That allows an overriding template to extend the original one and override
sections:

```j2
{% extends aep.templates.generic %}

{% block foo_bar_baz %}

## My mo-betta foo bar baz

Lorem ipsum dolor set something-not-amet
{% endblock %}
```

## Developer Setup

If you want to contribute to this project you will want to have a setup where
you can make changes to the code and see the result of your changes as soon as
possible. Here is a quick way to set up a local development environment that
will enable you to work on the code without having to reinstall the command
line scripts.

### Dependencies

You'll need venv. On Linux, install with,

```
sudo apt-get install python3-venv
```

### Running dev env

1. Check out the source

```bash
$ mkdir src
$ cd src
$ git clone https://github.com/aep-dev/site-generator.git
```

2. Setup python virtual environment

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
```

3. PIP Install with the editable option

```bash
$ pip install --editable .
```

4. Serve the aep.dev site

```bash
$ aep-site-serve /path/to/aep/data/on/your/system
```

[dataclasses]: https://docs.python.org/3/library/dataclasses.html
[jekyll]: https://jekyllrb.com/
[jinja2]: https://jinja.palletsprojects.com/en/2.11.x/
