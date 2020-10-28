import logging
import random

from .command import custom_migrate_slots
from .custom_node import CustomClusterNode
from .custom_reshard import CustomReshard
from .custom_util import CustomStd

total_slot_count = 16384
migrate_default_timeout = 60000
rebalance_default_threshold = 2


class RedisTrib(object):
    def __init__(self, opt={}):
        self.opt = opt
        self.nodes = []
        self.fix = False
        self.errors = []
        self.timeout = migrate_default_timeout
        self.cluster_error = False
        self.master_nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def reset_node(self):
        self.nodes = []

    def load_cluster_info_from_node(self, node_addr):
        logging.debug('load_cluster_info_from_node')
        node = CustomClusterNode(node_addr)
        node.load_info()
        self.reset_node()
        self.add_node(node)
        for friend in node.friends:
            if 'noaddr' in friend['flags'] or \
                    'disconnected' in friend['flags'] or \
                    'fail' in friend['flags']:
                continue
            fnode = CustomClusterNode(friend['addr'])
            fnode.load_info()
            self.add_node(fnode)
        self.populate_nodes_replicas_info()
        for node in self.nodes:
            if 'master' in node.info['flags']:
                self.master_nodes.append(node)

    def populate_nodes_replicas_info(self):
        # TODO
        pass

    def rebalance_cluster_cmd(self):
        ip = self.opt['ip']
        port = self.opt['port']
        threshold = rebalance_default_threshold

        self.load_cluster_info_from_node('%s:%s' % (ip, port))
        self.check_cluster()
        master_nodes = self.master_nodes
        nodes_involved = len(master_nodes)
        total_weight = len(master_nodes)
        threshold_reached = False
        for node in master_nodes:
            i = node.info
            expected = int(float(total_slot_count) / total_weight)
            slot_count = len(i['slots'].keys())
            b = slot_count - expected
            i['balance'] = b
            over_threshold = False
            if threshold > 0:
                if slot_count > 0:
                    err_perc = abs(100 - (100.0 * expected / slot_count))
                    print('err_perc:', err_perc)
                    over_threshold = err_perc > threshold
                elif expected > 0:
                    over_threshold = True
            if over_threshold:
                threshold_reached = over_threshold
        if not threshold_reached:
            print('*** No rebalancing needed! '
                  'All nodes are within the %s%% threshold' % threshold)
            return

        total_balance = sum(node.info['balance'] for node in master_nodes)
        while total_balance > 0:
            for node in master_nodes:
                if node.info['balance'] < 0 and total_balance > 0:
                    node.info['balance'] -= 1
                    total_balance -= 1
        master_nodes.sort(key=lambda x: x.info['balance'])
        print('>>> Rebalancing across %s nodes. Total weight = %s' % (
            nodes_involved, total_weight))

        for node in master_nodes:
            b = node.info['balance']
            name = node.info['name']
            print('%s balance is %s' % (name, b))

        dst_idx = 0
        src_idx = len(master_nodes) - 1
        while dst_idx < src_idx:
            dst = master_nodes[dst_idx]
            src = master_nodes[src_idx]
            num_slots = min([abs(dst.info['balance']),
                                abs(src.info['balance']), ])
            if num_slots > 0:
                src_name = src.info['name']
                dst_name = dst.info['name']
                print('Moving %s slots from %s to %s' % (
                    num_slots, src_name, dst_name))
                self.move_slots(src, dst, num_slots)

            dst.info['balance'] += num_slots
            src.info['balance'] -= num_slots
            dst_up = dst.info['balance'] == 0
            src_down = src.info['balance'] == 0
            dst_idx += dst_up
            src_idx -= src_down

    def show_reshard_table(self, table):
        for row in table:
            print('    Moving slot %s from %s' % (
                row['slot'],
                row['source'].info['name']
            ))

    def move_slots(self, src, dst, num_slots, quiet=False):
        move_target_slots = self.compute_single_reshard_table(src, num_slots)
        with CustomStd(quiet=quiet):
            custom_migrate_slots(src, dst, move_target_slots)

    def compute_single_reshard_table(self, src, num_slots):
        moved = []
        slots = src.info['slots']
        t = slots.keys()
        t.sort()
        for slot_num in t[0:int(num_slots)]:
            moved.append(slot_num)
        return moved

    def name_to_node(self, name):
        for node in self.nodes:
            if node.info['name'] == name:
                return node
        assert False
        return None

    def get_node_by_name(self, name):
        return self.name_to_node(name)

    def compute_reshard_table(
        self,
        src_node_ids,
        move_slot_count):
        src_list = list(map(self.name_to_node, src_node_ids))
        moved = []
        src_list.sort(key=lambda x: len(x.info['slots']), reverse=True)
        total_slots = sum(len(node.info['slots']) for node in src_list)
        if total_slots < move_slot_count:
            assert False

        ratio = float(move_slot_count) / total_slots
        target_count_list = []
        for i, node in enumerate(src_list):
            slots = node.info['slots']
            cur_slot_count = len(slots)
            target_count = int(ratio * cur_slot_count)
            # add one more if possible
            target_count = min(target_count + 1, cur_slot_count)
            target_count_list.append(target_count)
        src_count = len(src_list)
        while True:
            cur_sum = sum(target_count_list)
            if cur_sum == move_slot_count:
                break
            elif cur_sum < move_slot_count:
                exit(1)
            else:
                idx = random.randrange(src_count)
                if target_count_list[idx] > 0:
                    target_count_list[idx] -= 1

        for i, target_count in enumerate(target_count_list):
            node = src_list[i]
            slots = node.info['slots']
            t = slots.keys()
            t.sort()
            slot_num_list = []
            for slot_num in t[0:int(target_count)]:
                slot_num_list.append(slot_num)
            moved.append({'node': node, 'slot_num_list': slot_num_list})
        return moved

    def reshard_cluster_cmd(self, slots, src_node_ids, dest_node_id, src_all):
        ip = self.opt['ip']
        port = self.opt['port']
        self.load_cluster_info_from_node('%s:%s' % (ip, port))
        self.check_cluster()
        trib = self
        config = {
            'total_slot_count': 16384,
        }
        CustomReshard(
            trib, slots, src_node_ids, dest_node_id, src_all, config).run()

    def show_nodes(self):
        for node in self.nodes:
            print(node.info_string())

    def check_config_consistency(self):
        if not self.is_config_consistent():
            print("[ERR] Nodes don't agree about configuration!")
            self.cluster_error = True
            return False
        else:
            print('[OK] All nodes agree about slots configuration.')
            return True

    def check_open_slots(self):
        print('>>> Check for open slots...')
        open_slots = []
        for node in self.nodes:
            m_nodes = node.info['migrating']
            i_nodes = node.info['importing']
            if len(m_nodes) > 0:
                self.cluster_error = True
                print('[WARNING] Node %s has lots in migrating state' %
                      node.to_string())
                open_slots.append(m_nodes.keys())
            elif len(i_nodes) > 0:
                print('[WARNING] Node %s has lots in importing state' %
                      node.to_string())
                open_slots.append(i_nodes.keys())
                # TODO: implement fix option

    def covered_slots(self):
        slots = {}
        for node in self.nodes:
            cur_slots = node.info['slots'].copy()
            slots.update(cur_slots)
        return slots.keys()

    def check_slots_coverage(self):
        print('>>> Check slots coverage...')
        if total_slot_count == len(self.covered_slots()):
            print('[OK] All %s slots covered' % total_slot_count)
        else:
            print('[ERR] Not all %s slots are covered by nodes.' %
                  total_slot_count)

    def is_config_consistent(self):
        prev = None
        for node in self.nodes:
            cur = node.get_config_signature()
            if prev is None:
                prev = cur
            else:
                if prev != cur:
                    return False
        return True

    def check_cluster(self, quiet=False):
        n = self.nodes[0]
        self.cluster_error = False
        if not quiet:
            self.show_nodes()
        print('>>> Performing Cluster Check (using node %s)' % n.to_string())
        self.check_config_consistency()
        self.check_open_slots()
        self.check_slots_coverage()
        if self.cluster_error:
            print('*** Please fix your cluster problems before execution')
            exit(1)

    def is_exist_master_node_id(self, node_id):
        for node in self.master_nodes:
            if node_id == node.info['name']:
                return True
        return False


def rebalance_cluster_cmd(ip, port):
    logging.debug('rebalance')
    rt = RedisTrib({'ip': ip, 'port': port})
    rt.rebalance_cluster_cmd()
    return True


def reshard_cluster_cmd(ip, port, slots=0, dest_node_id=None, src_all=False):
    logging.debug('reshard')
    rt = RedisTrib({'ip': ip, 'port': port})
    src_node_ids = []
    rt.reshard_cluster_cmd(slots, src_node_ids, dest_node_id, src_all)
    return True


def check_cluster_cmd(ip, port):
    logging.debug('check_cluster')
    rt = RedisTrib({'ip': ip, 'port': port})
    rt.load_cluster_info_from_node('%s:%s' % (ip, port))
    rt.check_cluster()
    return True
