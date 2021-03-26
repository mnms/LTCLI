import os
import sys


class CustomStd(object):
    def __init__(self, quiet=True):
        self.devnull = open(os.devnull, 'w')
        if quiet:
            self._stdout = self.devnull or sys.stdout
            self._stderr = self.devnull or sys.stderr
        else:
            self._stdout = sys.stdout
            self._stderr = sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.devnull.close()


class PrettySlotGenerator(object):
    def __init__(self):
        self.pretty_list = []

    def generate(self, slots):
        key_list = slots.keys()
        key_list.sort()
        self.pretty_list = []
        buf = self._get_init_buf()
        for key in key_list:
            cur_state = buf['state']
            if cur_state == 'find_start':
                self._set_start_info(buf, key)
                continue
            elif cur_state == 'find_end':
                if self._is_continuous_number(buf['prev'], key):
                    buf['end'] = key
                    buf['prev'] = key
                    buf['count'] += 1
                else:
                    self._set_end_info(buf)
                    buf = self._get_init_buf()
                    self._set_start_info(buf, key)
            else:
                assert False
        return self.pretty_list

    def to_string(self, pretty_list=None):
        if pretty_list is None:
            pretty_list = self.pretty_list
        total = sum(int(v['count']) for v in pretty_list)
        msg = 'slots:'
        slot_str_list = []
        for item in pretty_list:
            s = item['start']
            e = item['end']
            slot_str_list.append('%d-%d' % (s, e))
        if len(slot_str_list) > 0:
            msg += ','.join(slot_str_list)
        msg += ' (%d slots)' % total
        return msg

    def _get_init_buf(self):
        buf = {
            'start': -1,
            'prev': -1,
            'end': -1,
            'count': 1,
            'state': 'find_start',
        }
        return buf

    def _set_start_info(self, buf, key):
        buf['state'] = 'find_end'
        buf['start'] = key
        buf['end'] = key
        buf['prev'] = key
        buf['count'] = 1
        self.pretty_list.append(buf)

    def _set_end_info(self, buf):
        buf['state'] = 'complete'
        buf['prev'] = -1

    def _is_continuous_number(self, prev, cur):
        diff = cur - prev
        return diff == 1
