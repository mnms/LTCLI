import os
from functools import reduce
import time

from ltcli import color, config, cluster_util, net, utils, message, ask_util
from ltcli.center import Center
from ltcli.log import logger
from ltcli.rediscli_util import RedisCliUtil
from ltcli.redistrib2.custom_trib import rebalance_cluster_cmd
from ltcli.exceptions import (
    ClusterIdError,
    ClusterNotExistError,
    LightningDBError,
    ClusterRedisError
)


def _change_cluster(cluster_id):
    if not isinstance(cluster_id, int):
        raise ClusterIdError(cluster_id)
    root_of_cli_config = config.get_root_of_cli_config()
    head_path = os.path.join(root_of_cli_config, 'HEAD')
    cluster_list = cluster_util.get_cluster_list()
    if cluster_id not in cluster_list + [-1]:
        raise ClusterNotExistError(cluster_id)
    with open(head_path, 'w') as fd:
        fd.write('%s' % cluster_id)


class Cluster(object):
    """Command Wrapper of trib.rb
    """

    def __init__(self, print_mode='screen'):
        self._print_mode = print_mode

    def stop(self, force=False, master=True, slave=True):
        """Stop cluster

        :param force: Force the cluster to shut down
        :param master: If exclude master cluster, set False
        :param slave: If exclude slave cluster, set False
        """
        if not isinstance(force, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='force')
            logger.error(msg)
            return
        if not isinstance(master, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='master')
            logger.error(msg)
            return
        if not isinstance(slave, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='slave')
            logger.error(msg)
            return
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.stop_redis(force, master=master, slave=slave)

    def start(self, profile=False, master=True, slave=True):
        """Start cluster

        :param master: If exclude master cluster, set False
        :param slave: If exclude slave cluster, set False
        """
        logger.debug("command 'cluster start'")
        if not isinstance(profile, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='profile')
            logger.error(msg)
            return
        if not isinstance(master, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='master')
            logger.error(msg)
            return
        if not isinstance(slave, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='slave')
            logger.error(msg)
            return
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.ensure_cluster_exist()
        if master:
            master_alive_count = center.get_alive_master_redis_count()
            master_alive_count_mine = center.get_alive_master_redis_count(
                check_owner=True
            )
            not_mine_count = master_alive_count - master_alive_count_mine
            if not_mine_count > 0:
                msg = message.get('error_cluster_start_master_collision')
                msg = '\n'.join(msg).format(count=not_mine_count)
                raise LightningDBError(11, msg)
        if slave:
            slave_alive_count = center.get_alive_slave_redis_count()
            slave_alive_count_mine = center.get_alive_slave_redis_count(
                check_owner=True
            )
            not_mine_count = slave_alive_count - slave_alive_count_mine
            if not_mine_count > 0:
                msg = message.get('error_cluster_start_slave_collision')
                msg = '\n'.join(msg).format(count=not_mine_count)
                raise LightningDBError(12, msg)
        center.backup_server_logs(master=master, slave=slave)
        center.create_redis_data_directory()

        # equal to cluster.configure()
        center.configure_redis()
        center.sync_conf(show_result=True)

        center.start_redis_process(profile, master=master, slave=slave)
        center.wait_until_all_redis_process_up(master=master, slave=slave)

    def create(self, yes=False):
        """Create cluster

        Before create cluster, all redis should be running.
        :param yes: skip confirm information
        """
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return

        m_count = len(center.master_host_list) * len(center.master_port_list)
        if m_count < 3:
            msg = message.get('error_master_redis_less_than_3')
            raise ClusterRedisError(msg)

        # if need to cluster start
        alive_count = center.get_alive_all_redis_count()
        my_alive_count = center.get_alive_all_redis_count(check_owner=True)
        if alive_count != my_alive_count:
            msg = message.get('error_cluster_start_port_collision')
            raise ClusterRedisError(msg)
        all_count = len(center.all_host_list)
        if alive_count < all_count:
            logger.debug('cluster start in create')
            # init
            center.backup_server_logs()
            center.create_redis_data_directory()

            # cluster configure
            center.configure_redis()
            center.sync_conf(show_result=True)

            # cluster start
            center.start_redis_process()
            center.wait_until_all_redis_process_up()

        key = 'cluster-node-timeout'
        m_hosts = center.master_host_list
        m_ports = center.master_port_list
        origin_m_value = center.cli_config_get(key, m_hosts[0], m_ports[0])
        if not origin_m_value:
            msg = "RedisConfigKeyError(master): '{}'".format(key)
            logger.warning(msg)
        s_hosts = center.slave_host_list
        s_ports = center.slave_port_list
        if s_hosts and s_ports:
            origin_s_value = center.cli_config_get(key, s_hosts[0], s_ports[0])
            if not origin_s_value:
                msg = "RedisConfigKeyError(slave): '{}'".format(key)
                logger.warning(msg)
        if origin_m_value:
            # cli config set cluster-node-timeout 2000
            logger.debug('set cluster node time out 2000 for create')
            center.cli_config_set_all(key, '2000', m_hosts, m_ports)
            if s_hosts and s_ports and origin_s_value:
                center.cli_config_set_all(key, '2000', s_hosts, s_ports)
        center.create_cluster(yes)
        if origin_m_value:
            # cli config restore cluster-node-timeout
            logger.debug('restore cluster node time out')
            center.cli_config_set_all(key, origin_m_value, m_hosts, m_ports)
            if s_hosts and s_ports and origin_s_value:
                v = origin_s_value
                center.cli_config_set_all(key, v, s_hosts, s_ports)

    def clean(self, logs=False):
        """Clean cluster

        Delete redis config, data, node configuration.
        :param log: Delete log of redis
        """
        if not isinstance(logs, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='logs')
            logger.error(msg)
            return
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if success:
            center.stop_redis(force=True)
        if logs:
            center.remove_all_of_redis_log_force()
            return
        center.cluster_clean()
        msg = message.get('apply_after_restart')
        logger.info(msg)

    def use(self, cluster_id):
        """Change selected cluster

        :param cluster_id: target cluster #
        """
        _change_cluster(cluster_id)
        cluster_id = '-' if cluster_id == -1 else cluster_id
        msg = message.get('use_cluster').format(cluster_id=cluster_id)
        logger.info(msg)

    def ls(self):
        """Get cluster list
        """
        logger.info(cluster_util.get_cluster_list())

    def restart(
        self,
        force_stop=False,
        reset=False,
        cluster=False,
        profile=False,
        yes=False,
    ):
        """Restart cluster

        :param force_stop: Force the cluster to shuto down
        :param reset: Delete redis config, data, node configuration
        :param cluster: Create cluster after cluster start
        :param yes: Skip confirm information when cluster create
        """
        if not isinstance(force_stop, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='force-stop')
            logger.error(msg)
            return
        if not isinstance(reset, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='reset')
            logger.error(msg)
            return
        if not reset and cluster:
            msg = message.get('error_option_use_with')
            msg = msg.format(option='cluster', with_option='reset')
            logger.error(msg)
            return
        if not isinstance(cluster, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='cluster')
            logger.error(msg)
            return
        if not cluster and yes:
            msg = message.get('error_option_use_with')
            msg = msg.format(option='yes', with_option='cluster')
            msg = "option '--yes' can used only with option '--cluster'"
            logger.error(msg)
            return
        if not isinstance(yes, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='yes')
            logger.error(msg)
            return
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.stop_redis(force=force_stop)
        if reset:
            self.clean()
        self.start(profile=profile)
        if cluster:
            self.create(yes=yes)

    def configure(self):
        """Configure cluster

        Make conf file of redis with redis properties information.
        """
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.configure_redis()
        center.sync_conf(show_result=True)

    def rowcount(self):
        """Query and show cluster row count
        """
        logger.debug('rowcount')
        # open-redis-cli-all info Tablespace | grep totalRows | awk -F ',
        # ' '{print $4}' | awk -F '=' '{sum += $2} END {print sum}'
        ret = RedisCliUtil.command_all_async('info Tablespace', slave=False)
        outs = ''
        for _, host, port, res, stdout in ret:
            if res == 'OK':
                outs = '\n'.join([outs, stdout])
            else:
                logger.warning("FAIL {}:{} {}".format(host, port, stdout))
        lines = outs.splitlines()
        key = 'totalRows'
        filtered_lines = (filter(lambda x: key in x, lines))
        ld = RedisCliUtil.to_list_of_dict(filtered_lines)
        # row_count = reduce(lambda x, y: {key: int(x[key]) + int(y[key])}, ld)
        row_count = reduce(lambda x, y: x + int(y[key]), ld, 0)
        self._print(row_count)

    def scaleout(self):
        """ Scale out the cluster

        """
        # settings
        curr_cluster_id = config.get_cur_cluster_id()
        scaleout_hosts = ask_util.hosts_to_scaleout()

        scaleout_size = len(scaleout_hosts)
        if scaleout_size == 0:
            msg = message.get('empty_nodes_to_scaleout')
            raise ClusterRedisError(msg)

        path_of_fb = config.get_path_of_fb(curr_cluster_id)
        props_path = path_of_fb['redis_properties']
        m_key = 'sr2_redis_master_hosts'
        m_hosts = config.get_props(props_path, m_key, [])
        s_key = 'sr2_redis_slave_hosts'
        s_hosts = config.get_props(props_path, s_key, [])

        prev_hosts = m_hosts
        already_included = False
        for node in scaleout_hosts:
            if node in m_hosts:
                already_included = True
                break

        if already_included == False:
            m_hosts = m_hosts + scaleout_hosts
            config.make_key_enable(props_path, m_key)
            config.set_props(props_path, m_key, m_hosts)

            s_hosts = s_hosts + scaleout_hosts
            config.make_key_enable(props_path, s_key)
            config.set_props(props_path, s_key, s_hosts)

        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return

        m_ports = center.master_port_list
        s_ports = center.slave_port_list

        center.ensure_cluster_exist()

        # confirm info
        result = center.confirm_node_port_info()
        if not result:
            msg = message.get('cancel')
            logger.warning(msg)
            return

        # backup logs
        center.backup_server_logs()
        center.create_redis_data_directory()

        # configure
        center.configure_redis()
        center.sync_conf()

        # run added nodes(master/slave)
        center.start_redis_process()
        center.wait_until_all_redis_process_up()

        # cluster meet master nodes. 'cluster meet' for slaves is handled in replicate.
        center.meet_new_nodes(scaleout_hosts)

        # change redis config temporarily
        key = 'cluster-node-timeout'
        origin_s_value = center.cli_config_get(key, s_hosts[0], s_ports[0])
        if not origin_s_value:
            msg = "RedisConfigKeyError: '{}'".format(key)
            logger.warning(msg)
        if origin_s_value:
            # cli config set cluster-node-timeout 2000
            logger.debug('set cluster node time out 2000 for create')
            center.cli_config_set_all(key, '2000', s_hosts, s_ports)

        # do replicate
        center.replicate_with_scaleout_nodes(prev_hosts, scaleout_hosts)

        # rollback redis config
        if origin_s_value:
            # cli config restore cluster-node-timeout
            logger.debug('restore cluster node time out')
            center.cli_config_set_all(key, origin_s_value, s_hosts, s_ports)

        # scale out
        self.rebalance(m_hosts[0], m_ports[0])
        # check_cluster_cmd(m_hosts[0], m_ports[0])

        self._print("OK")

    def rebalance(self, ip, port):
        """Rebalance cluster

        :param ip: rebalance target ip
        :param port: rebalance target port
        """
        rebalance_cluster_cmd(ip, port)

    def add_slave(self, yes=False):
        """Add slave of cluster

        Add slaves to cluster that configured master only.
        :param yes: Skip confirm information
        """
        logger.debug('add_slave')
        if not isinstance(yes, bool):
            msg = message.get('error_option_type_not_boolean')
            msg = msg.format(option='yes')
            logger.error(msg)
            return
        center = Center()
        center.update_ip_port()
        # check
        s_hosts = center.slave_host_list
        s_ports = center.slave_port_list
        if not s_hosts:
            msg = message.get('error_slave_host_empty')
            raise ClusterRedisError(msg)
        if not s_ports:
            msg = message.get('error_slave_port_empty')
            raise ClusterRedisError(msg)
        success = center.check_hosts_connection(hosts=s_hosts)
        if not success:
            return
        center.ensure_cluster_exist()
        slave_alive_count = center.get_alive_slave_redis_count()
        slave_alive_count_mine = center.get_alive_slave_redis_count(
            check_owner=True
        )
        not_mine_count = slave_alive_count - slave_alive_count_mine
        if not_mine_count > 0:
            msg = message.get('error_cluster_start_slave_collision')
            msg = '\n'.join(msg).format(count=not_mine_count)
            raise LightningDBError(12, msg)

        # confirm info
        result = center.confirm_node_port_info(skip=yes)
        if not result:
            msg = message.get('cancel')
            logger.warning(msg)
            return
        # clean
        center.cluster_clean(master=False)
        # backup logs
        center.backup_server_logs(master=False)
        center.create_redis_data_directory(master=False)
        # configure
        center.configure_redis(master=False)
        center.sync_conf()
        # start
        center.start_redis_process(master=False)
        center.wait_until_all_redis_process_up()

        # change redis config temporarily
        key = 'cluster-node-timeout'
        origin_s_value = center.cli_config_get(key, s_hosts[0], s_ports[0])
        if not origin_s_value:
            msg = "RedisConfigKeyError: '{}'".format(key)
            logger.warning(msg)
        if origin_s_value:
            # cli config set cluster-node-timeout 2000
            logger.debug('set cluster node time out 2000 for create')
            center.cli_config_set_all(key, '2000', s_hosts, s_ports)
        # create
        center.replicate()
        if origin_s_value:
            # cli config restore cluster-node-timeout
            logger.debug('restore cluster node time out')
            center.cli_config_set_all(key, origin_s_value, s_hosts, s_ports)

    def failover(self):
        """Replace disconnected master with slave

        If disconnected master comes back to live, it become slave.
        """
        center = Center()
        center.update_ip_port()
        master_obj_list = center.get_master_obj_list()
        msg = color.yellow(message.get('error_no_alive_slave_for_failover'))
        all_alive = True
        for node in master_obj_list:
            if node['status'] != 'connected':
                all_alive = False
                success = False
                for slave in node['slaves']:
                    if slave['status'] == 'connected':
                        msg2 = message.get('redis_failover').format(
                            slave_addr=slave['addr'],
                            master_addr=node['addr']
                        )
                        logger.info(msg2)
                        stdout = center.run_failover(
                            slave['addr'],
                            take_over=True
                        )
                        if stdout != 'OK':
                            continue
                        logger.info('OK')
                        success = True
                        break
                if not success:
                    logger.info(msg.format(node['addr']))
        if all_alive:
            msg = message.get('already_all_master_alive')
            logger.info(msg)

    def failback(self):
        """Restart disconnected redis
        """
        center = Center()
        center.update_ip_port()
        master_obj_list = center.get_master_obj_list()
        disconnected_list = []
        paused_list = []
        for master in master_obj_list:
            if master['status'] == 'disconnected':
                disconnected_list.append(master['addr'])
            if master['status'] == 'paused':
                paused_list.append(master['addr'])
            for slave in master['slaves']:
                if slave['status'] == 'disconnected':
                    disconnected_list.append(slave['addr'])
                if slave['status'] == 'paused':
                    paused_list.append(slave['addr'])
        classified_disconnected_list = {}
        classified_paused_list = {}
        for disconnected in disconnected_list:
            host, port = disconnected.split(':')
            if host not in classified_disconnected_list:
                classified_disconnected_list[host] = []
            classified_disconnected_list[host].append(port)
        for paused in paused_list:
            host, port = paused.split(':')
            if host not in classified_paused_list:
                classified_paused_list[host] = []
            classified_paused_list[host].append(port)
        current_time = time.strftime("%Y%m%d-%H%M", time.gmtime())
        for host, ports in classified_disconnected_list.items():
            msg = message.get('redis_run')
            msg = msg.format(host=host, ports='|'.join(ports))
            logger.info(msg)
            center.run_redis_process(host, ports, False, current_time)
        for host, ports in classified_paused_list.items():
            msg = message.get('redis_restart')
            msg = msg.format(host=host, ports='|'.join(ports))
            logger.info(msg)
            center.stop_redis_process(host, ports)
            center.run_redis_process(host, ports, False, current_time)
        if not classified_disconnected_list and not classified_paused_list:
            msg = message.get('already_all_redis_alive')
            logger.info(msg)

    def tree(self):
        """The results of 'cli cluster nodes' are displayed in tree format
        """
        center = Center()
        center.update_ip_port()
        master_node_list = center.get_master_obj_list()
        output_msg = []
        for master_node in master_node_list:
            addr = master_node['addr']
            status = master_node['status']
            msg = '{}({})'.format(addr, status)
            if status == 'disconnected':
                msg = color.red(msg)
            if status == 'paused':
                msg = color.yellow(msg)
            output_msg.append(msg)
            for slave_node in master_node['slaves']:
                addr = slave_node['addr']
                status = slave_node['status']
                msg = '{}({})'.format(addr, status)
                if status == 'disconnected':
                    msg = color.red(msg)
                if status == 'paused':
                    msg = color.yellow(msg)
                output_msg.append('|__ ' + msg)
            output_msg.append('')
        logger.info(color.ENDC + '\n'.join(output_msg))

    def cstop(self, master=True, slave=True):
        """Stop current masters or slaves
        """
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.stop_current_nodes(master, slave)

    def cstart(self, master=True, slave=True):
        """Start current masters or slaves
        """
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        center.start_current_nodes(master, slave)

    def _print(self, text):
        if self._print_mode == 'screen':
            logger.info(text)

    def restore(self, cluster_id, tag=None):
        """Restore cluster

        :param cluster_id: target cluster id
        :param tag: Tag of backup, if omitted, restore the most recent backup file
        """
        logger.debug('cluster restore: cluster_id={}, tag={}'.format(
            cluster_id,
            tag
        ))
        if not cluster_util.validate_id(cluster_id):
            raise ClusterIdError(cluster_id)
        # find restore folder with tag (local)
        path_of_fb = config.get_path_of_fb(cluster_id)
        cluster_backup_path = path_of_fb['cluster_backup_path']
        if tag is None:
            backup_list = os.listdir(cluster_backup_path)
            pattern = 'cluster_{}_bak_'.format(cluster_id)
            filtered = filter(lambda x: x.startswith(pattern), backup_list)
            sorted_list = sorted(list(filtered))
            if not sorted_list:
                msg = message.get('error_not_found_any_backup')
                logger.error('BackupNotExistError: ' + msg)
                return
            tag = sorted_list[-1]
            logger.debug("tag option is empty, auto select: {}".format(tag))
        cluster_restore_dir = tag
        backup_path = os.path.join(cluster_backup_path, cluster_restore_dir)
        if not os.path.isdir(backup_path):
            msg = message.get('error_not_found_backup').format(tag=tag)
            logger.error('BackupNotExistError: ' + msg)
            return

        # get hosts from cluster props
        props_path = os.path.join(
            backup_path,
            'tsr2-assembly-1.0.0-SNAPSHOT',
            'conf',
            'redis.properties'
        )
        hosts = config.get_props(props_path, 'sr2_redis_master_hosts', [])

        # check status of hosts
        success = Center().check_hosts_connection(hosts, True)
        if not success:
            msg = message.get('error_exist_unavailable_host')
            logger.error(msg)
            return
        logger.debug('Connection of all hosts ok.')
        success = Center().check_include_localhost(hosts)
        if not success:
            msg = message.get('error_not_include_localhost')
            logger.error(msg)
            return

        # check all host tag folder: OK / NOT FOUND
        msg = message.get('check_backup_info')
        logger.info(msg)
        buf = []
        for host in hosts:
            client = net.get_ssh(host)
            if not net.is_dir(client, backup_path):
                logger.debug('cannot find backup dir: {}-{}'.format(
                    host,
                    cluster_restore_dir
                ))
                buf.append([host, color.red('NOT FOUND')])
            client.close()
        if buf:
            utils.print_table([['HOST', 'RESULT'] + buf])
            return
        logger.info('OK')

        # backup cluster
        new_tag = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        cluster_backup_dir = 'cluster_{}_bak_{}'.format(cluster_id, new_tag)
        for host in hosts:
            Center().cluster_backup(host, cluster_id, cluster_backup_dir)

        # restore cluster
        command = "cp -r {} {}/cluster_{}".format(
            backup_path,
            path_of_fb['base_directory'],
            cluster_id
        )
        for host in hosts:
            msg = message.get('restore_cluster')
            msg = msg.format(tag=cluster_backup_dir, host=host)
            logger.info(msg)
            client = net.get_ssh(host)
            net.ssh_execute(client, command)
            client.close()
            logger.info("OK")

    def version(self):
        """Get version of lightningDB
        """
        cluster_id = config.get_cur_cluster_id()
        tsr2_home = config.get_tsr2_home(cluster_id)
        with open(os.path.join(tsr2_home, "VERSION"), "r") as version_file:
            lines = version_file.readlines()
            logger.info("".join(lines).strip())

    def delete(self, cluster_id):
        """Delete cluster

        It is automatically backed up with timestamps as tags
        :param cluster_id: target cluster id
        """
        if not cluster_util.validate_id(cluster_id):
            raise ClusterIdError(cluster_id)
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if success:
            center.stop_redis(force=True)
        path_of_fb = config.get_path_of_fb(cluster_id)
        props_path = path_of_fb['redis_properties']
        hosts = config.get_props(props_path, 'sr2_redis_master_hosts', [])
        if not center.check_include_localhost(hosts):
            hosts += [config.get_local_ip()]
        tag = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        cluster_backup_dir = 'cluster_{}_bak_{}'.format(cluster_id, tag)
        for host in hosts:
            center.cluster_backup(host, cluster_id, cluster_backup_dir)
        msg = message.get('cluster_delete_complete')
        msg = msg.format(cluster_id=cluster_id)
        logger.info(msg)
