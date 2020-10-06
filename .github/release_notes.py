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

import collections
import subprocess
import sys
import typing


class Changelog:
    def __init__(self, git_log: str):
        self._commits = {}
        for commit in git_log.split('\n'):
            # Spilt the type from the message.
            type_ = 'other'
            message = commit
            if ':' in message:
                type_, message = commit.split(':', 1)

            # If the change is breaking, note it separately.
            if type_.endswith('!'):
                type_ = 'breaking'

            # Add the commit to the appropriate bucket.
            self._commits.setdefault(type_, [])
            self._commits[type_].append(message.strip())

    @property
    def markdown(self):
        """Return the changelog Markdown for the GitHub release."""
        answer = ''
        headers = collections.OrderedDict((
            ('breaking', 'Breaking Changes'),
            ('feat', 'Features'),
            ('fix', 'Bugfixes'),
            ('refactor', 'Refactors'),
            ('docs', 'Documentation'),
        ))
        for key, header in headers.items():
            if key in self._commits:
                answer += f'## {header}\n\n'
                for cmt in self._commits[key]:
                    answer += f'- {cmt}\n'
                answer += '\n'
        return answer.strip()


def exec(cmd: typing.List[str]) -> str:
    """Execute the given command and return the output.

    If the command returns a non-zero exit status, fail loudly and exit.
    """
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f'Error running {cmd[0]}: {proc.stderr}', file=sys.stderr)
        sys.exit(proc.returncode)
    return proc.stdout.strip()


if __name__ == '__main__':
    # Get the previous tag and the current tag.
    revs = exec(['git', 'rev-list', '--simplify-by-decoration',
                 '--tags', '--max-count=2']).split('\n')
    new_tag, prev_tag = (exec(['git', 'describe', '--tags', r]) for r in revs)
    commit_range = f'{prev_tag}..{new_tag}'
    if len(sys.argv) > 1:
        commit_range = sys.argv[1]

    # Get the changelog between those two tags.
    cl = Changelog(exec(['git', 'log', commit_range,
                         '--oneline', '--pretty=format:%s']))

    # Print the Markdown using GitHub's special syntax.
    #
    # Note: %0A must be used for newline.
    # https://github.community/t/set-output-truncates-multiline-strings/16852
    print('::set-output name=release_notes::{rel_notes}'.format(
        rel_notes=cl.markdown.replace('\n', '%0A')
    ))
