# aip.dev static site generator

This is the site generator for [aip.dev](https://aip.dev) and its forks. It
takes AIP files in a git repository and outputs a static website.

## Why?

We are not fans of rolling our own tools when off-the-shelf alternatives exist.
However, the AIP project has grown sufficiently mature to warrant it.

GitHub Pages normally automatically builds documentation with [Jekyll][], but
as the AIP system has grown, we are beginning to reach the limits of what
Jekyll can handle, and other off-the-shelf generators had similar issues:

- AIP adoption is handled through fork-and-merge and top-down configuration
  files will lead to repetitive merge conflicts.
- Our grouping and listing logic has grown complicated, and had to be
  maintained using complex and error-prone Liquid templates.
- Jekyll is extensible but GitHub requires specific Jekyll plugins, meaning we
  can not use off-the-shelf solutions for planned features (e.g. tabbed code
  examples).
- Lack of meaningful build CI caused failures.
- Working with the development environment was (really) slow.

There are some additional advantages that we unlock with a custom generator:

- We can override segments of AIPs using template extensions in new files
  rather than modifying existing files.
- We can provide useful abstractions for common deviations between companies
  (e.g. case systems) that minimize the need to fork AIPs.
- We can customize the Markdown parsing where necessary (tabs, hotlinking,
  etc.).

## How does it work?

This is essentially split into three parts:

- Python code (`aip_site/`):
  - The majority of the code is models (`aip_site/models/`) that represent the
    fundamental concept of an AIP site. These are rolled up into a singleton
    object called `Site` that is used everywhere. All models are
    [dataclasses][] that get sent to templates.
  - There is also a publisher class (`aip_site/publisher.py`) that is able to
    slurp up a repo of AIPs and build a static site.
  - There is some server code (`aip_site/server.py`) that can run a development
    server.
  - All remaining files are thin support code to avoid repeating things in or
    between the above.
- Templates (`support/templates/`) are [Jinja2][] templates containing (mostly)
  HTML that makes up the layout of the site.
- Assets (`support/assets/` and `support/scss/`) are other static files. SCSS
  is automatically compiled into CSS at publication.

Of the models, there are three models in particular that matter:

- **Site:** A singleton that provides access to all scopes, AIPs, and static
  pages. This is sent to every template as the `site` variable.
- **AIP:** A representation of a single AIP, including both content and
  metadata. This is sent to the AIP rendering template as the `aip` variable.
- **Scope:** A group of AIPs that apply to a particular scope. The "general"
  scope is special, and is the "root" group. This is sent to the AIP _listing_
  template as the `scope` variable.

Templates are [jinja2][] files in the `templates/` directory.

**Note:** We run Jinja in with "strict undefined", so referencing an undefined
variable in a template is a hard error rather than an empty string.

### Entry points

There are two entry points for the app. The _publisher_
(`aip_site/publisher.py`) is the program that iterates over the relevant
directories, renders HTML files, and writes them out to disk. The _app_
(`aip_site/server.py`) is a lightweight Flask app that provides a development
server.

These entry points are routed through the CLI file (`aip_site/cli.py`); when
this application is installed using pip, it makes the `aip-site-gen`
(publisher) and `aip-site-serve` (server) commands available.

### Extensions

This site generator includes a basic extension system for AIPs. When processing
AIPs as plain Markdown files, it will make any Markdown (level 2 or 3) header
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
{% extends aip.templates.generic %}

{% block foo_bar_baz %}

## My mo-betta foo bar baz

Lorem ipsum dolor set something-not-amet
{% endblock %}
```

[dataclasses]: https://docs.python.org/3/library/dataclasses.html
[jekyll]: https://jekyllrb.com/
[jinja2]: https://jinja.palletsprojects.com/en/2.11.x/
