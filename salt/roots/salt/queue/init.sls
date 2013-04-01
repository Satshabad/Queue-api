include:
  - webserver

git:
  pkg:
    - installed

https://github.com/Satshabad/Queue-API.git:
  git.latest:
    - target: /srv/www/queue_app
    - require:
      - pkg: git 

python-pip:
  pkg.installed

queue:
  pip.installed:
    - requirements: /srv/www/queue_app/requirements.txt
    - require:
      - pkg: python-pip
      - git: https://github.com/Satshabad/Queue-API.git 

/srv/www/queue_app:
  file.directory:
    - user: www-data
    - group: www-data
    - mode: 760
    - makedirs: True

supervisor:
  pkg.installed

/etc/supervisord.conf:
  file.managed:
    - source: salt://queue/supervisord.conf
