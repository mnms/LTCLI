import os
import shutil


from ltcli import config, editor, ask_util, message
from ltcli.log import logger
from ltcli.center import Center


class Conf(object):
    """Edit conf file

    Open conf file with editor. Sync to all hosts after edit.
    """
    def __init__(self):
        pass

    def cluster(self):
        """Edit 'redis.properties' of cluster
        """
        cluster_id = config.get_cur_cluster_id()
        path_of_fb = config.get_path_of_fb(cluster_id)
        target_path = path_of_fb['redis_properties']
        self._edit_conf(target_path, syntax='sh')
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        success = center.sync_file(target_path)
        if success:
            msg = message.get('complete_conf_edit')
            logger.info(msg)

    def master(self):
        """Edit 'redis-master.conf.template'
        """
        cluster_id = config.get_cur_cluster_id()
        path_of_fb = config.get_path_of_fb(cluster_id)
        target_path = path_of_fb['master_template']
        self._edit_conf(target_path, syntax='sh')
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        success = center.sync_file(target_path)
        if success:
            msg = message.get('complete_conf_edit')
            logger.info(msg)

    def thriftserver(self):
        """Edit 'thriftserver.properties'
        """
        cluster_id = config.get_cur_cluster_id()
        path_of_fb = config.get_path_of_fb(cluster_id)
        target_path = path_of_fb['thrift_properties']
        self._edit_conf(target_path, syntax='sh')
        center = Center()
        center.update_ip_port()
        success = center.check_hosts_connection()
        if not success:
            return
        success = center.sync_file(target_path)
        if success:
            msg = message.get('complete_conf_edit')
            logger.info(msg)

    def ths(self):
        """Edit 'thriftserver.properties'
        """
        self.thriftserver()

    def _edit_conf(self, target_path, syntax=None):
        tmp_target_path = target_path + '.tmp'
        if os.path.exists(tmp_target_path):
            msg = message.get('ask_load_history_of_previous_modification')
            yes = ask_util.askBool(msg)
            if not yes:
                os.remove(tmp_target_path)
        if not os.path.exists(tmp_target_path):
            shutil.copy(target_path, tmp_target_path)
        editor.edit(tmp_target_path, syntax=syntax)
        shutil.copy(tmp_target_path, target_path)
        os.remove(tmp_target_path)
