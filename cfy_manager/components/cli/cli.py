#########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import errno
import logging
from os.path import join, expanduser
from getpass import getuser

from ..components_constants import SOURCES, SECURITY, MASTER_IP
from ..base_component import BaseComponent
from ..service_names import CLI, MANAGER, CLUSTER
from ...config import config
from ...logger import (get_logger,
                       set_file_handlers_level,
                       get_file_handlers_level)
from ...utils import common
from ...constants import EXTERNAL_CERT_PATH
from ...utils.install import yum_install, yum_remove

logger = get_logger(CLI)


class CliComponent(BaseComponent):

    def __init__(self, skip_installation):
        super(CliComponent, self).__init__(skip_installation)

    def _install(self):
        source_url = config[CLI][SOURCES]['cli_source_url']
        yum_install(source_url)

    def _set_colors(self, is_root):
        """
        Makes sure colors are enabled by default in cloudify logs via CLI
        """

        home_dir = '/root' if is_root else expanduser('~')
        sed_cmd = 's/colors: false/colors: true/g'
        config_path = join(home_dir, '.cloudify', 'config.yaml')
        cmd = "/usr/bin/sed -i -e '{0}' {1}".format(sed_cmd, config_path)

        # Adding sudo manually, because common.sudo doesn't work well with sed
        cmd = "sudo {0}".format(cmd) if is_root else cmd
        common.run([cmd], shell=True)

    def _configure(self):
        username = config[MANAGER][SECURITY]['admin_username']
        password = config[MANAGER][SECURITY]['admin_password']

        manager = config[MANAGER]['cli_local_profile_host_name']
        if config[CLUSTER][MASTER_IP]:
            manager = config[CLUSTER][MASTER_IP]
        use_cmd = ['cfy', 'profiles', 'use', manager,
                   '--skip-credentials-validation']

        ssl_enabled = \
            'on' if config[MANAGER][SECURITY]['ssl_enabled'] else 'off'

        set_cmd = [
            'cfy', 'profiles', 'set', '-u', username,
            '-p', password, '-t', 'default_tenant',
            '-c', EXTERNAL_CERT_PATH, '--ssl', ssl_enabled
        ]

        current_user = getuser()

        logger.info('Setting CLI for the current user ({0})...'.format(
            current_user))
        # we don't want the commands with the password to be printed
        # to log file
        current_level = get_file_handlers_level()
        set_file_handlers_level(logging.ERROR)
        common.run(use_cmd)
        common.run(set_cmd)
        self._set_colors(is_root=False)

        if current_user != 'root':
            logger.info('Setting CLI for the root user...')
            for cmd in (use_cmd, set_cmd):
                root_cmd = ['sudo', '-u', 'root'] + cmd
                common.run(root_cmd)
            self._set_colors(is_root=True)
        set_file_handlers_level(current_level)

    def install(self):
        logger.notice('Installing Cloudify CLI...')
        self._install()
        self._configure()
        logger.notice('Cloudify CLI successfully installed')

    def configure(self):
        logger.notice('Configuring Cloudify CLI...')
        self._configure()
        logger.notice('Cloudify CLI successfully configured')

    def remove(self):
        profile_name = config[MANAGER]['cli_local_profile_host_name']

        def _remove_profile_and_check(cli_cmd):
            proc = common.run(cli_cmd, ignore_failures=True)
            if proc.returncode == 0:
                logger.notice('CLI profile removed')
            else:
                logger.warning('Failed removing CLI profile (rc={})'.format(
                    proc.returncode))

        try:
            logger.notice('Removing CLI profile...')

            cmd = ['cfy', 'profiles', 'delete', profile_name]
            _remove_profile_and_check(cmd)

            current_user = getuser()
            if current_user != 'root':
                logger.notice('Removing CLI profile for root user...')
                root_cmd = ['sudo', '-u', 'root'] + cmd
                _remove_profile_and_check(root_cmd)
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                logger.warning('Could not find the `cfy` executable; it has '
                               'most likely been removed already or never '
                               'installed due to an error; skipping')
            else:
                raise

        logger.notice('Removing Cloudify CLI...')
        yum_remove('cloudify')
        logger.notice('Cloudify CLI successfully removed')
