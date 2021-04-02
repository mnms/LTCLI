import os
import sys

from prompt_toolkit.styles import Style
from terminaltables import AsciiTable

from ltcli import config, editor
from ltcli.log import logger
from ltcli.exceptions import ConvertError


class TermColor:
    """This is for term text color
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def green(msg):
        return TermColor.OKGREEN + msg + TermColor.ENDC

    @staticmethod
    def fail(msg):
        return TermColor.FAIL + msg + TermColor.ENDC

    @staticmethod
    def blue(msg):
        return TermColor.OKBLUE + msg + TermColor.ENDC


class RangeChecker(object):
    """This class for checking range of index

    Update min max value
    """
    def __init__(self):
        self.min_index = 99999999
        self.max_index = 0

    def check(self, cur_index):
        """Update min, max index value
        :param cur_index: cur index
        """
        if self.min_index > cur_index:
            self.min_index = cur_index
        if self.max_index < cur_index:
            self.max_index = cur_index


def print_table(meta):
    """Print data as table format
    """
    table = AsciiTable(meta)
    print(table.table)


def get_ip_port_tuple_list(ip_list, port_list):
    """Convert as ip | port tuple data(list)
    """
    targets = []
    for ip in ip_list:
        for port in port_list:
            targets.append((ip, port))
    return targets


def get_ip_port_dict_list(ip_list, port_list):
    """Convert as ip | port dict list
    """
    targets = []
    for ip in ip_list:
        for port in port_list:
            targets.append({'host': ip, 'port': port})
    return targets


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class DuplicatedError(Error):
    def __init__(self, target):
        self.target = target
        logger.error('DuplicatedError: %s' % target)


class CommandError(Error):
    def __init__(self, exit_status, command, hostname, port):
        self.exit_status = exit_status
        self.command = command
        self.hostname = hostname
        self.port = port
        msg = [
            'CommandError:',
            'exit_status={}'.format(exit_status),
            'command={}'.format(command),
            'host:port={}:{}'.format(hostname, port)
        ]
        logger.error('\n'.join(msg))


# table print
def tprint(dictionary, header=['key', 'value']):
    """Table print dictionary

    :param dictionary: dictionary
    :param header: header
    """
    items = dictionary.items()
    sorted_list = sorted(items, key=lambda x: x[1])
    tr = TableReport(header)
    tr.data = sorted_list
    tr.print_out()


def tprint_list(rows, header=['key', 'value1', 'value2']):
    """Table print list

    :param rows: list
    :param header: header
    """
    tr = TableReport(header)
    tr.data = rows
    tr.print_out()


class TableReport(object):
    """This is for logging important information and print out as table format
    """
    def __init__(self, column):
        self.header = [column]
        self.data = []

    def append(self, item):
        """Append data

        :param item: data
        """
        self.data.append(item)

    def success(self):
        """Append success event as green color
        """
        self.data.append([
            sys._getframe(1).f_code.co_name,
            TermColor.green('ok')])

    def fail(self):
        """Append fail event as red color
        """
        self.data.append([
            sys._getframe(1).f_code.co_name,
            TermColor.fail('fail')])

    def print_out(self):
        """Print out result
        """
        table = AsciiTable(self.header + self.data)
        print(table.table)


def clear_screen():
    """Clear screen
    """
    os.system('cls' if os.name == 'nt' else 'clear')


style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


def get_full_path_of_props(cluster_id=-1, target='config'):
    """Get full path of props

    When user wants to edit props files, use it.

    :param cluster_id: cluster #
    :param target: target config (config | master | slave | thriftserver)
    """
    targets = {
        'config': 'config.yaml',
        'master': 'tsr2-conf/redis-master.conf.template',
        'thriftserver': 'tsr2-conf/thriftserver.properties',
    }
    home = config.get_repo_cluster_path(cluster_id)
    f = targets[target]
    full_path = os.path.join(home, f)
    return full_path


def open_vim_editor(target='config'):
    """Open vim editor
    :param target: config | master | slave | thriftserver
    """
    cluster_id = config.get_cur_cluster_id()
    full_path = get_full_path_of_props(cluster_id, target)
    editor.edit(full_path)


def make_export_envs(ip, port):
    """Make export env
    """
    envs = config.get_env_dict(ip, port)
    cmd = '''\
export SR2_REDIS_HOME={sr2_redis_home} ; \
export SR2_REDIS_BIN={sr2_redis_bin} ; \
export SR2_REDIS_LIB={sr2_redis_lib} ; \
export SR2_REDIS_CONF={sr2_redis_conf} ; \
export SR2_REDIS_LOG={sr2_redis_log} ; \
export SR2_REDIS_DATA={sr2_redis_data} ; \
export SR2_REDIS_DUMP={sr2_redis_dump} ; \
export SR2_REDIS_DB_PATH={sr2_redis_db_path} ; \
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{ld_library_path} ; \
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:{dyld_library_path}''' \
        .format(**envs)
    return cmd


def convert_list_2_hyphen(ports):
    '''
    converted as shown below
    [1, 2, 3, 5, 7, 8, 10]
    =>
    ['1-3', '5', '7-8', 10]
    '''
    logger.debug('ports: {}'.format(ports))
    ret = []
    s = ports[0]
    pre = ports[0] - 1
    try:
        for port in ports:
            if pre != port - 1:
                if s != pre:
                    ret.append('{}-{}'.format(s, pre))
                else:
                    ret.append(str(s))
                s = port
            pre = port
        if s != pre:
            ret.append('{}-{}'.format(s, pre))
        else:
            ret.append(str(s))
        logger.debug('converted: {}'.format(ret))
        return ret
    except Exception:
        raise ConvertError("Invalid ports: '{}'".format(ports))


def is_number(target):
    try:
        target = target.decode('utf-8')
    except AttributeError:
        pass
    return target.isdecimal()


def to_str(target):
    if isinstance(target, bytes):
        target = target.decode('utf-8')
    return str(target)


def int_2_time(v):
    v = int(v)
    if v == 0:
        return '0secs'
    ONE_MIN = 60
    ONE_HOUR = ONE_MIN * 60
    ONE_DAY = ONE_HOUR * 24
    ret = []
    if v >= ONE_DAY:
        days = v // ONE_DAY
        v -= days * ONE_DAY
        ret.append('{}days'.format(days))
    if v >= ONE_HOUR:
        hours = v // ONE_HOUR
        v -= hours * ONE_HOUR
        ret.append('{}hours'.format(hours))
    if v >= ONE_MIN:
        mins = v // ONE_MIN
        v -= mins * ONE_MIN
        ret.append('{}mins'.format(mins))
    if v > 0:
        ret.append('{}secs'.format(v))
    return ' '.join(ret)


def int_2_bytes(v):
    v = int(v)
    if v == 0:
        return '0b'
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024
    ret = []
    if v >= GB:
        gb = v // GB
        v -= gb * GB
        ret.append('{}gb'.format(gb))
    if v >= MB:
        mb = v // MB
        v -= mb * MB
        ret.append('{}mb'.format(mb))
    if v >= KB:
        kb = v // KB
        v -= kb * KB
        ret.append('{}kb'.format(kb))
    if v > 0:
        ret.append('{}b'.format(v))
    return ' '.join(ret)


def convert_2_human_readable(key, value):
    enable_human_readable = {
        'flash-db-ttl': 'date',
        'flash-db-size-limit': 'byte',
        'force_flush_slaves_outputbuffer_size': 'byte',
        'maxmemory': 'byte'
    }
    if key not in enable_human_readable:
        logger.debug('{} is not support human readable')
        return value
    if enable_human_readable[key] == 'date':
        converted = int_2_time(value)
        logger.debug('{} convert: {}'.format(value, converted))
        return converted
    if enable_human_readable[key] == 'byte':
        converted = int_2_bytes(value)
        logger.debug('{} convert: {}'.format(value, converted))
        return converted
