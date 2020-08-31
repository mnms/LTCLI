from ltcli import utils, color, message
from ltcli.log import logger
from ltcli.rediscli import (
    RedisCliCluster,
    RedisCliConfig,
    RedisCliInfo,
    RedisCliUtil
)


# pylint: disable=redefined-builtin
# need to parameter all for cli options
def _command(sub_cmd, all, host, port):
    if all:
        RedisCliUtil.command_all(sub_cmd=sub_cmd, formatter=utils.print_table)
    else:
        RedisCliUtil.command(sub_cmd=sub_cmd, host=host, port=port)


def ping(host=None, port=None, all=False):
    """Send ping command

    :param all: If true, send command to all
    :param host: host info for redis
    :param port: port info for redis
    """
    if not isinstance(all, bool):
        msg = message.get('error_option_type_not_boolean').format(option='all')
        logger.error(msg)
        return
    if (not host or not port) and not all:
        msg = message.get('use_host_port_or_option_all')
        logger.error(msg)
        return
    if all:
        meta = []
        ret = RedisCliUtil.command_all_async('ping 2>&1')
        pong_cnt = 0
        for m_s, host, port, result, _ in ret:
            addr = '{}:{}'.format(host, port)
            if result == 'OK':
                pong_cnt += 1
            else:
                meta.append([m_s, addr, color.red('FAIL')])
        if meta:
            utils.print_table([['TYPE', 'ADDR', 'RESULT']] + meta)
        msg = message.get('counting_alive_redis')
        msg = msg.format(alive=pong_cnt, total=len(ret))
        logger.info(msg)
        return
    if host and port:
        _command('ping', False, host, port)


def reset_oom(all=False, host=None, port=0):
    """Send reset oom command

    :param all: If true, send command to all
    :param host: host info for redis
    :param port: port info for redis
    """
    if not isinstance(all, bool):
        msg = message.get('error_option_type_not_boolean').format(option='all')
        logger.error(msg)
        return
    sub_cmd = 'resetOom'
    _command(sub_cmd, all, host, port)


def reset_info(key, all=False, host=None, port=0):
    """Send reset info

    :param key: resetting target key string
    :param all: If true, send command to all
    :param host: host info for redis
    :param port: port info for redis
    """
    if not isinstance(all, bool):
        msg = message.get('error_option_type_not_boolean').format(option='all')
        logger.error(msg)
        return
    sub_cmd = 'resetInfo %s' % key
    _command(sub_cmd, all, host, port)


def metakeys(key, all=False, host=None, port=0):
    """Get metakeys

    :param key: target key
    :param all: If true, send command to all
    :param host: host info for redis
    :param port: port info for redis
    """
    if not isinstance(all, bool):
        msg = message.get('error_option_type_not_boolean').format(option='all')
        logger.error(msg)
        return
    sub_cmd = 'metakeys "%s"' % key
    _command(sub_cmd, all, host, port)


def relmodeltest(host='localhost', port=7379):
    """Execute unit test

    :param host: host info for redis
    :param port: port info for redis
    """
    sub_cmd = 'relmodeltest'
    _command(sub_cmd, False, host, port)


class Cli(object):
    """Command wrapper of redis-cli
    """

    def __init__(self):
        self.info = RedisCliInfo()
        self.config = RedisCliConfig()
        self.cluster = RedisCliCluster()
        self.ping = ping
        self.reset_oom = reset_oom
        self.reset_info = reset_info
        self.metakeys = metakeys
        self.relmodeltest = relmodeltest
