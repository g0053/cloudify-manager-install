import os
from tempfile import mkstemp
from os.path import join, isdir, islink

from ..service_names import POSTGRESQL

from ... import constants
from ...config import config
from ...logger import get_logger

from ...utils import common
from ...utils.systemd import systemd
from ...utils.deploy import copy_notice
from ...utils.install import yum_install
from ...utils.files import ln, write_to_file


SYSTEMD_SERVICE_NAME = 'postgresql-9.5'
LOG_DIR = join(constants.BASE_LOG_DIR, POSTGRESQL)

PGSQL_LIB_DIR = '/var/lib/pgsql'
PGSQL_USR_DIR = '/usr/pgsql-9.5'
PS_HBA_CONF = '/var/lib/pgsql/9.5/data/pg_hba.conf'
PGPASS_PATH = join(constants.CLOUDIFY_HOME_DIR, '.pgpass')

PG_PORT = 5432

logger = get_logger(POSTGRESQL)


def _install():
    logger.info('Installing PostgreSQL...')
    sources = config[POSTGRESQL]['sources']
    for source in sources.values():
        yum_install(source)


def _init_postgresql():
    logger.info('Initializing PostreSQL DATA folder...')
    postgresql95_setup = join(PGSQL_USR_DIR, 'bin', 'postgresql95-setup')
    try:
        common.sudo(command=[postgresql95_setup, 'initdb'])
    except Exception:
        logger.debug('PostreSQL DATA folder already initialized...')
        pass

    logger.debug('Installing PostgreSQL service...')
    systemd.enable(SYSTEMD_SERVICE_NAME, append_prefix=False)
    systemd.restart(SYSTEMD_SERVICE_NAME, append_prefix=False)

    logger.info('Setting PostgreSQL logs path...')
    ps_95_logs_path = join(PGSQL_LIB_DIR, '9.5', 'data', 'pg_log')
    common.mkdir(LOG_DIR)
    if not isdir(ps_95_logs_path) and not islink(join(LOG_DIR, 'pg_log')):
        ln(source=ps_95_logs_path, target=LOG_DIR, params='-s')

    logger.info('Starting PostgreSQL service...')
    systemd.restart(SYSTEMD_SERVICE_NAME, append_prefix=False)


def _read_hba_lines():
    fd, temp_hba_path = mkstemp()
    os.close(fd)
    common.copy(PS_HBA_CONF, temp_hba_path)
    common.chmod('777', temp_hba_path)
    with open(temp_hba_path, 'r') as f:
        lines = f.readlines()
    common.remove(temp_hba_path)
    return lines


def _write_new_hba_file(lines):
    fd, temp_hba_path = mkstemp()
    os.close(fd)
    with open(temp_hba_path, 'w') as f:
        for line in lines:
            if line.startswith(('host', 'local')):
                line = line.replace('ident', 'md5')
            f.write(line)
    return temp_hba_path


def _update_configuration():
    logger.info('Updating PostgreSQL configuration...')
    logger.debug('Modifying {0}'.format(PS_HBA_CONF))
    common.copy(PS_HBA_CONF, '{0}.backup'.format(PS_HBA_CONF))
    lines = _read_hba_lines()
    temp_hba_path = _write_new_hba_file(lines)
    common.move(temp_hba_path, PS_HBA_CONF)
    common.chown('postgres', 'postgres', PS_HBA_CONF)


def _create_postgres_pass_file():
    logger.info('Creating postgresql pgpass file: {0}'.format(PGPASS_PATH))
    pg_config = config[POSTGRESQL]
    pgpass_content = '{host}:{port}:{db_name}:{user}:{password}'.format(
        host=pg_config['host'],
        port=PG_PORT,
        db_name=pg_config['db_name'],
        user=pg_config['username'],
        password=pg_config['password']
    )
    pgpass_path = join(constants.CLOUDIFY_HOME_DIR, '.pgpass')
    write_to_file(pgpass_content, pgpass_path)
    common.chmod('400', pgpass_path)
    common.chown(
        constants.CLOUDIFY_USER,
        constants.CLOUDIFY_GROUP,
        pgpass_path
    )

    logger.debug('Postgresql pass file {0} created'.format(PGPASS_PATH))


def _create_default_db():
    pg_config = config[POSTGRESQL]
    if not pg_config['create_db']:
        return
    logger.info(
        'Creating default PostgreSQL DB: {0}...'.format(pg_config['db_name'])
    )
    script_path = join(
        constants.COMPONENTS_DIR,
        POSTGRESQL,
        'scripts',
        'create_default_db.sh'
    )
    tmp_script_path = common.temp_copy(script_path)
    common.chmod('+x', tmp_script_path)
    common.sudo(
        'su - postgres -c "{cmd} {db} {user} {password}"'.format(
            cmd=tmp_script_path,
            db=pg_config['db_name'],
            user=pg_config['username'],
            password=pg_config['password'])
    )


def _configure():
    copy_notice(POSTGRESQL)
    _init_postgresql()
    _update_configuration()
    _create_postgres_pass_file()

    systemd.restart(SYSTEMD_SERVICE_NAME, append_prefix=False)
    systemd.verify_alive(SYSTEMD_SERVICE_NAME, append_prefix=False)

    _create_default_db()


def install():
    logger.notice('Installing PostgreSQL...')
    _install()
    _configure()
    logger.notice('PostgreSQL installed successfully')


def configure():
    logger.notice('Configuring PostgreSQL...')
    _configure()
    logger.notice('PostgreSQL configured successfully')
