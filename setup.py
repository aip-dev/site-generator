# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os

from setuptools import find_packages, setup  # type: ignore


PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(PACKAGE_ROOT, 'VERSION'), 'r') as version_file:
    VERSION = version_file.read().strip()

with io.open(os.path.join(PACKAGE_ROOT, 'README.md'), 'r') as readme_file:
    long_description = readme_file.read().strip()

setup(
    name='aip-site-generator',
    version=VERSION,
    license='Apache 2.0',
    author='Luke Sneeringer',
    author_email='lukesneeringer@google.com',
    url='https://github.com/aip-dev/site-generator.git',
    packages=find_packages(exclude=['tests']),
    description='Static site generator for aip.dev and forks.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points="""[console_scripts]
        aip-site-gen=aip_site.cli:publish
        aip-site-serve=aip_site.cli:serve
    """,
    platforms='Posix; MacOS X',
    include_package_data=True,
    install_requires=(
        'click==7.1.2',
        'flask==1.1.2',
        'itsdangerous==1.1.0',
        'jinja2==2.11.2',
        'markdown==3.3.3',
        'markupsafe==1.1.1',
        'pygments==2.7.3',
        'pymdown-extensions==8.1',
        'pyscss==1.3.7',
        'pyyaml==5.3.1',
        'six==1.15.0',
        'werkzeug==1.0.1',
    ),
    python_requires='>=3.8',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Code Generators',
    ),
    zip_safe=False,
)
