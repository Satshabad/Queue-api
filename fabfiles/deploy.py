from fabric.api import run, env, local, task, put
from fabric.context_managers import cd
from fabtools.vagrant import vagrant
from fabric.contrib.files import exists

API_HOME = "/srv/www/queue/api/"
REPO = "https://github.com/Satshabad/Queue-API.git"

@task
def prod():
    ensure_dir_exists(API_HOME)
    install_git()
    get_code()
    config_sentry_dsn()
    dev()

@task
def dev():
    install_make()
    ensure_dir_exists(API_HOME)
    ensure_dir_exists("{}logs".format(API_HOME))
    install_queue_api()
    install_web_server()
    ensure_db_exists()
    run_web_server()

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
    put("fabfiles/config/sentry_dns.py", API_HOME, use_sudo=True)

def run_web_server():
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
    put("fabfiles/config/nginx.conf", "/etc/nginx/sites-available/default", use_sudo=True)
    put("fabfiles/config/nginx.conf", "/etc/nginx/sites-enabled/default", use_sudo=True)

def install_git():
    run("sudo apt-get -y install git")

def get_code():
    with cd(API_HOME):
        if run('ls'):
            run('sudo git pull origin master')
        else:
            run("sudo git clone {} .".format(REPO))

def install_as_package():
    with cd(API_HOME):
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
