from __future__ import print_function

import redis
from .custom_util import PrettySlotGenerator


class CustomClusterNode(object):
    def __init__(self, addr):
        s = addr.split(':')
        if len(s) < 2:
            print('Invalid Addr (given as %s) - use IP:Port format' % addr)
            exit(1)
        ip = s[0]
        port = int(s[1])
        info = {
            'ip': ip,
            'port': port,
            'slots': {},
            'migrating': {},
            'importing': {},
            'replicate': False,
        }
        self.info = info
        self.all_info_list = []
        self.friends = []
        self.dirty = False
        self.r = None
        self.ip = ip
        self.port = port
        self.connect()

    def connect(self):
        self.r = redis.Redis(host=self.ip, port=self.port)
        self.r.ping()

    def to_string(self):
        return '%s:%s' % (self.info['ip'], self.info['port'])

    def info_string(self, info=None):
        if info is None:
            info = self.info
        tag = 'S'
        if self._is_master(info):
            tag = 'M'
        slots = info['slots']
        slot_info = self._get_pretty_slot_info(slots)
        msg = '%s: %s %s %s %s' % (
            tag,
            info['name'],
            info['ip'],
            info['port'],
            slot_info
        )
        return msg

    def load_info(self, o={}):
        conn = self.r
        nodes_res_text = conn.execute_command('cluster nodes')
        info_res_text = conn.execute_command('cluster info')
        self.all_info_list = []
        self.info = {}
        self._load_info(nodes_res_text, info_res_text, o)
        return self

    def get_config_signature(self):
        self.load_info()
        signature = ''
        sorted_info_list = sorted(self.all_info_list, key=lambda x: x['name'])
        for info in sorted_info_list:
            msg = self.info_string(info)
            if msg.startswith('M'):
                signature += (msg + '|')
        return signature

    @staticmethod
    def _get_pretty_slot_info(slots):
        slots = slots
        g = PrettySlotGenerator()
        g.generate(slots)
        return g.to_string()

    def _load_info(self, nodes_res_text, info_res_text, o):
        s = nodes_res_text.split('\n')
        for row in s:
            if len(row) > 0:
                self._load_info_row(row, info_res_text, o)

    def _load_info_row(self, row, info_res_text, o):
        arr = row.split(' ')
        name = arr[0]
        addr = arr[1]
        if '@' in addr:
            addr = addr.split('@')[0]
        s = addr.split(':')
        if len(s) < 2:
            print('Invalid Addr (given as %s) - use IP:Port format' % addr)
            exit(1)
        ip = s[0]
        port = int(s[1])
        flags = arr[2]
        my_master_id = arr[3]
        ping_sent = arr[4]
        ping_recv = arr[5]
        config_epoch = arr[6]
        link_status = arr[7]
        slots = arr[8:]
        info = {
            'name': name,
            'ip': ip,
            'port': port,
            'addr': addr,
            'flags': flags.split(','),
            'replicate': my_master_id == '-',
            'ping_sent': int(ping_sent),
            'ping_recv': int(ping_recv),
            'link_status': link_status,
            'config_epoch': config_epoch,
            'migrating': {},
            'importing': {},
            'my_master_id': my_master_id,
            'slots': {},
        }
        self._load_slots(info, slots)
        self._load_cluster_info_text(info, info_res_text)
        self.all_info_list.append(info)
        if 'myself' in info['flags']:
            self.info = info
        else:
            self.friends.append(info)

    def _is_master(self, info=None):
        if info is None:
            info = self.info
        return 'master' in info['flags']

    @staticmethod
    def _load_cluster_info_text(info, info_res_text):
        items = info_res_text.split('\n')
        for item in items:
            if len(item.strip()) == 0:
                continue
            k, v = item.split(':')
            k = k.strip()
            v = v.strip()
            if k == 'cluster_state':
                info[k] = v
            else:
                info[k] = int(v)

    @staticmethod
    def _load_slots(info, slots):
        for slot in slots:
            if len(slot) == 0:
                continue
            if '->-' in slot:
                slot = slot.replace('[', '').replace(']', '')
                no, dst = slot.split('->-')
                info['migrating'][int(no)] = dst
            elif '-<-' in slot:
                slot = slot.replace('[', '').replace(']', '')
                no, src = slot.split('-<-')
                info['importing'][int(no)] = src
            elif '-' in slot:
                start, stop = slot.split('-')
                CustomClusterNode._add_slots(info, start, stop)
            else:
                CustomClusterNode._add_slots(info, slot, slot)

    @staticmethod
    def _add_slots(info, start, stop):
        for i in range(int(start), int(stop) + 1):
            info['slots'][i] = True
