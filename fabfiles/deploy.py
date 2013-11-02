from fabric.api import run, env, local, task, put
from fabric.context_managers import cd
from fabtools.vagrant import vagrant
from fabric.contrib.files import exists

API_HOME = "/srv/www/queue/api/"
WEB_HOME = "/srv/www/queue/website/"
API_REPO = "https://github.com/Satshabad/Queue-api.git"
WEB_REPO = "https://github.com/Satshabad/Queue-website"


@task
def prod_deploy_all():
    ensure_dir_exists(API_HOME)
    ensure_dir_exists(WEB_HOME)
    install_git()
    get_code()
    config_sentry_dsn()
    dev()


@task
def prod_deploy_code():
    get_code()
    install_as_package()
    restart_web_servers()


@task
def dev():
    install_make()
    ensure_dir_exists(API_HOME)
    ensure_dir_exists(WEB_HOME)
    ensure_dir_exists("{}logs".format(API_HOME))
    install_queue_api()
    install_web_server()
    ensure_db_exists()
    restart_web_servers()


@task
def restart():
    install_as_package()
    restart_web_servers()


def install_queue_api():
    install_pip()
    install_python_dev()
    install_requirements()
    install_as_package()


def install_web_server():
    install_uwsgi()
    config_uwsgi()

    install_nginx()
    config_nginx()


def config_sentry_dsn():
    put("fabfiles/config/sentry_dsn.py", API_HOME, use_sudo=True)


def restart_web_servers():
    run("sudo service uwsgi restart")
    run("sudo service nginx restart")


def ensure_dir_exists(path):
    if not exists(path):
        run('sudo mkdir -p {}'.format(path))


def ensure_db_exists():
    run("sudo apt-get -y install sqlite3")
    with cd(API_HOME):
        if not exists("api/queue.db"):
            run("sudo python api/scripts/init_db.py")


def install_uwsgi():
    run("sudo apt-get -y install python-pip")
    run("sudo apt-get -y install python-dev")
    run("sudo pip install uwsgi")


def config_uwsgi():
    put("fabfiles/config/uwsgi.conf", "/etc/init/uwsgi.conf", use_sudo=True)


def install_nginx():
    run("sudo apt-get -y install nginx")


def config_nginx():
    put("fabfiles/config/nginx.conf",
        "/etc/nginx/sites-available/default", use_sudo=True)
    put("fabfiles/config/nginx.conf",
        "/etc/nginx/sites-enabled/default", use_sudo=True)


def install_git():
    run("sudo apt-get -y install git")


def get_code():
    with cd(API_HOME):
        if run('ls'):
            run('sudo git pull origin master')
        else:
            run("sudo git clone {} .".format(API_REPO))

    with cd(WEB_HOME):
        if run('ls'):
            run('sudo git pull origin master')
        else:
            run("sudo git clone {} .".format(WEB_REPO))

def install_as_package():

    with cd(API_HOME):
        if exists('build'):
            run("rm -r build")
        if exists('dist'):
            run("rm -r dist")
        if exists('api.egg-info'):
            run("rm -r api.egg-info")

        run("sudo python setup.py install")


def install_requirements():
    with cd(API_HOME):
            run("sudo pip install -r requirements.txt")


def install_pip():
    run("sudo apt-get -y install python-pip")


def install_make():
    run("sudo apt-get -y install make")


def install_python_dev():
    run("sudo apt-get -y update")
    run("sudo apt-get -y install python-dev")
