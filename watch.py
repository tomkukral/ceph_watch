#!/usr/bin/env python3

from time import sleep

import subprocess
import re


class CephReader():
    """Reads ceph -w output and parse it"""

    def __init__(self, cmd='./ceph.sh'):
        self.cmd = cmd
        self.line = None

    def read(self):
        p = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        while True:
            self.line = p.stdout.readline().strip()
            self.parse()

    def parse(self):
        # pgmap v28143095: 320 pgs: 320 active+clean; 289 GB data, 875 GB used, 2722 GB / 3597 GB avail; 34637 B/s wr, 5 op/s\n

        regexp = r'.*pgmap v(?P<pgmap>[\d]*): (?P<pgs>[\d]*) pgs: (?P<tmp_pg_states>.*?); (?P<data>[\d]* [MGT]B) data, (?P<used>[\d]* [MGT]B) used, (?P<avail>[\d]* [MGT]B) / (?P<max_used>[\d]* [MGT]B) avail'
        regexp_pg_state = r'(?P<count>[\d]*) (?P<state>.*)'

        line_match = re.match(regexp, self.line)

        if line_match:
            self.parsed = line_match.groupdict()
            self.parsed['pg'] = {}

            for i in line_match.group('tmp_pg_states').split(','):
                pg_state_match = re.match(regexp_pg_state, i.strip())
                if pg_state_match:
                    self.parsed['pg'][pg_state_match.group('state')] = pg_state_match.group('count')

            self.export()

        else:
            print('not matched: ' + self.line)

    def export(self):
        """Export metrics to file"""

        metrics = []

        for k, v in self.parsed.items():
            if not k.startswith('tmp_'):
                # print strings
                if type(v) == str:
                    if v.isdigit():
                        metrics.append('ceph_{} {}'.format(k, v))

                    else:
                        # convert to bytes if MB|GB|TB
                        size_match = re.match('(?P<size>[\d]*) (?P<unit>.*)', v)
                        if size_match:
                            if size_match.group('unit') == 'MB':
                                ratio = 10**6
                            elif size_match.group('unit') == 'GB':
                                ratio = 10**9
                            elif size_match.group('unit') == 'TB':
                                ratio = 10**9

                            if ratio:
                                metrics.append(
                                    'ceph_{} {}'.format(k, int(size_match.group('size'))*ratio)
                                )
                # pg states
                if k == 'pg':
                    for state, count in v.items():
                        metrics.append('ceph_pg_state{{state="{}"}} {}'.format(state, count))

        print('\n'.join(metrics))

if __name__ == '__main__':
    a = CephReader()
    a.read()
