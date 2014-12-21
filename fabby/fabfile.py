from fabric.api import env, local, run, sudo
from gh import some_settings
import os

env.user = 'ubuntu'
env.key_filename = ['~/.ssh/chefbox.pem']

#put in your public ip address for your aws box
#env.hosts = ['54.171.201.222'] #chefbox

env.hosts = ['54.154.28.16']
project_root = "~/%s" % some_settings['name']
activate_script = os.path.join(project_root, 'env/bin/activate')

#  hardcoded for now
repo_root = os.path.join(project_root, 'testapp')


def update():
    sudo('apt-get -y update', pty=True)


def upgrade():
    sudo('apt-get -y upgrade', pty=True)


def make_proj_root():
    run("mkdir -p %s " % project_root)


def virtualenv(command, use_sudo=False):
    if use_sudo:
        func = sudo
    else:
        func = run
    func(". %s && %s" % (activate_script, command))


def makemigrations():
    virtualenv("cd %s && python manage.py makemigrations" % repo_root)


def migrate():
    virtualenv("cd %s && python manage.py migrate" % repo_root)


def createsuperuser():
    virtualenv("cd %s && python manage.py createsuperuser" % repo_root)


def startproject(name):
    virtualenv("cd %s && django-admin startproject %s" % (project_root, name))


def setup_gunicorn():
    virtualenv("pip install gunicorn ")


def setup_mysql():
    sudo("debconf-set-selections <<< 'mysql-server mysql-server/root_password password lululu1'")
    sudo("debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password lululu1'")
    sudo("apt-get install libmysqlclient-dev mysql-client-core-5.5 -y", pty=True)
    virtualenv("pip install MySQL-python==1.2.3")
    sudo("apt-get -y install mysql-server", pty=True)
    run('mysql -u root -p%s -e "create database IF NOT EXISTS dbname";' % ("'lululu1'"))
    run('mysql -u root -p%s -e "grant all on dbname.* to root@localhost identified by %s ";' % ("'lululu1'", "'lululu1'"))


def setup_postgres():
    sudo("apt-get -y install postgresql-9.3 postgresql-server-dev-9.3")


def make_logs():
    run("cd %s && mkdir -p logs && touch logs/gunicorn_supervisor.log" % repo_root )
    sudo("touch %s " % (repo_root + '/logs/nginx-access.log'))
    sudo("touch %s " % (repo_root + '/logs/nginx-error.log'))


def update_supervisor():
    sudo('supervisorctl reread && supervisorctl update')


def install_nginx():
    sudo('apt-get install nginx -y')


def restart_ngninx():
    sudo('service nginx restart')


def setup_django():
    update()
    upgrade()
    #going with mysql for now, will leave postgres stuff in there anyway
    sudo('apt-get -y install python-pip git python-virtualenv python-dev mercurial meld supervisor')
    make_proj_root()
    run('cd %s && virtualenv env' % project_root)
    #setup_postgres()
    setup_mysql()

    run('cd %s && git clone https://charlesfaustin@bitbucket.org/charlesfaustin/testapp.git' % project_root)

    virtualenv("pip install -r %s " % (repo_root + '/requirements.txt'))
    virtualenv("pip install setproctitle")

    #running fab to install locally on remote machine is pretty easy
    # http://stackoverflow.com/a/6769071/2049067

    makemigrations()
    migrate()
    #createsuperuser()
    setup_gunicorn()
    #will have to copy supervisor config & gunicorn_start file from repo, into the right places
    # then change permissions etc
    # need ot make /home/ubuntu/uwotmate/testapp/run/ & put gunicorn.sock file in it
    run("cp %s /home/ubuntu/uwotmate/env/bin" % (repo_root + '/configs/gunicorn_start'))
    sudo ("chmod u+x /home/ubuntu/uwotmate/env/bin/gunicorn_start")

    make_logs()

    install_nginx()

    sudo("cp %s /etc/nginx/sites-available" % (repo_root + '/configs/testapp'))
    try:
        sudo("rm /etc/nginx/sites-enabled/default")
    except:
        pass
    sudo("ln -s /etc/nginx/sites-available/testapp /etc/nginx/sites-enabled/testapp")

    restart_ngninx()

    #copy supervisor files into place
    sudo("cp %s /etc/supervisor/conf.d" % (repo_root + '/configs/testapp.conf'))

    update_supervisor()
    sudo("supervisorctl restart testapp")

    #also look at https://github.com/jcalazan/ansible-django-stack

