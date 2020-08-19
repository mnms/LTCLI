from __future__ import print_function

from terminaltables import AsciiTable

from ltcli import config, utils, color, message as m
from ltcli.center import Center
from ltcli.rediscli_util import RedisCliUtil
from ltcli.log import logger


class RedisCliInfo(object):
    def __init__(self):
        pass

    def all(self, host=None, port=None):
        """Command: redis-cli info all"""
        RedisCliUtil.command(sub_cmd='info', host=host, port=port)

    def memory(self, host=None, port=None):
        """Command: redis-cli info memory"""
        RedisCliUtil.command(sub_cmd='info memory', host=host, port=port)

    def eviction(self, host=None, port=None):
        """Command: redis-cli info eviction"""
        RedisCliUtil.command(sub_cmd='info eviction', host=host, port=port)

    def keyspace(self, host=None, port=None):
        """Command: redis-cli info keyspace"""
        RedisCliUtil.command(sub_cmd='info keyspace', host=host, port=port)

    def tablespace(self, host=None, port=None):
        """Command: redis-cli info tablespace"""
        RedisCliUtil.command(sub_cmd='info tablespace', host=host, port=port)

    def replication(self, host=None, port=None):
        """Command: redis-cli info replication"""
        RedisCliUtil.command('info replication', host=host, port=port)

    def alert(self, host=None, port=None):
        """Command: redis-cli info alert"""
        RedisCliUtil.command('info alert', host=host, port=port)


class RedisCliCluster(object):
    def __init__(self):
        pass

    def info(self):
        """Command: redis-cli cluster info"""
        RedisCliUtil.command('cluster info')

    def nodes(self):
        """Command: redis-cli cluster nodes"""
        RedisCliUtil.command('cluster nodes')

    def slots(self):
        """Command: redis-cli cluster slots"""
        def formatter(outs):
            lines = outs.splitlines()
            replicas = config.get_replicas()
            column_count = 2 + 2 * (replicas + 1)
            row_count = len(lines) / column_count
            header = [['start', 'end', 'm_ip', 'm_port']]
            remain = column_count - 4
            data = []
            for i in range(0, remain / 2):
                header[0].append('s_ip_%d' % i)
                header[0].append('s_port_%d' % i)
            for i in range(0, row_count):
                data.append(lines[i * column_count: column_count * (i + 1)])
            data.sort(key=lambda x: int(x[0]))
            table = AsciiTable(header + data)
            print(table.table)

        RedisCliUtil.command('cluster slots', formatter=formatter)


class RedisCliConfig(object):
    def __init__(self):
        pass

    def no_print(self, output):
        pass

    def _is_cluster_unit(self, key):
        return key in ['flash-db-size-limit']

    def _convert_2_cluster_limit(self, ret):
        combined = 0
        for m_s, _, _, _, message in ret:
            if message and m_s == 'Master':
                _, value = message.split('\n')
                if utils.is_number(value):
                    combined += int(value)
        return combined

    def get(self, key, all=False, host=None, port=None):
        """Command: redis-cli config get

        :param key: redis config keyword
        :param all: If true, send command to all redis
        :param host: host info for redis
        :param port: port info for redis
        """
        if not isinstance(all, bool):
            msg = m.get('error_option_type_not_boolean')
            msg = msg.format(options='all')
            logger.error(msg)
            return
        if (not host or not port) and not all:
            msg = m.get('use_host_port_or_option_all')
            logger.error(msg)
            return
        sub_cmd = 'config get "{key}" 2>&1'.format(key=key)
        if all:
            meta = []
            ret = RedisCliUtil.command_all_async(sub_cmd)
            for m_s, host, port, result, message in ret:
                addr = '{}:{}'.format(host, port)
                if result == 'OK':
                    if message:
                        _, value = message.split('\n')
                        meta.append([m_s, addr, value])
                    else:
                        meta.append([m_s, addr, color.red('Invalid Key')])
                else:
                    meta.append([m_s, addr, color.red(result)])
            utils.print_table([['TYPE', 'ADDR', 'RESULT']] + meta)
        else:
            output = RedisCliUtil.command(
                sub_cmd=sub_cmd,
                host=host,
                port=port,
                formatter=self.no_print)
            output = output.strip()
            if output:
                key, value = output.split('\n')
                logger.info(value)
            else:
                msg = m.get('error_invalid_key').format(key=key)
                logger.error(msg)

    def set(self, key, value, all=False, save=False, host=None, port=None):
        """Command: redis-cli config set

        :param key: target key
        :param value: value to set
        :param save: If true, save value to config file
        :param all: If true, send command to all redis
        :param host: host info for redis
        :param port: port info for redis
        """
        if not isinstance(all, bool):
            msg = m.get('error_option_type_not_boolean')
            msg = msg.format(options='all')
            logger.error(msg)
            return
        if not isinstance(save, bool):
            msg = m.get('error_option_type_not_boolean')
            msg = msg.format(options='save')
            logger.error(msg)
            return
        if (not host or not port) and not all:
            msg = m.get('use_host_port_or_option_all')
            logger.error(msg)
            return
        sub_cmd = 'config set {key} {value} 2>&1'.format(key=key, value=value)
        if all:
            meta = []
            ret = RedisCliUtil.command_all_async(sub_cmd)
            ok_cnt = 0
            for m_s, host, port, result, message in ret:
                addr = '{}:{}'.format(host, port)
                if result == 'OK':
                    if utils.to_str(message) == 'OK':
                        ok_cnt += 1
                    else:
                        meta.append([m_s, addr, color.red(message)])
                else:
                    meta.append([m_s, addr, color.red('FAIL')])
            if meta:
                utils.print_table([['TYPE', 'ADDR', 'RESULT']] + meta)
            logger.info('success {}/{}'.format(ok_cnt, len(ret)))
        else:
            output = RedisCliUtil.command(
                sub_cmd=sub_cmd,
                host=host,
                port=port,
                formatter=self.no_print)
            output = output.strip()
            if output == "OK":
                logger.info(output)
            else:
                logger.error(output)
        if save:
            RedisCliUtil.save_redis_template_config(key, value)
            center = Center()
            center.update_ip_port()
            success = center.check_hosts_connection()
            if not success:
                return
            center.configure_redis()
            center.sync_conf()
