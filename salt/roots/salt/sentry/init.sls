include:
  - postgres

pipinstalled:
  pkg:
    - installed
    - names:
      - python-pip

virtualenv:
  pip.installed:
    - require:
      - pkg: pipinstalled


/srv/www/sentry:
  virtualenv.managed:
    - no_site_packages: True
    - requirements: salt://sentry/requirements.txt
    - distribute: True
  require:
    - pkg: pipinstalled
    - pkg: postgres-pkgs
    - pip: virtualenv


pg_sentry:
  postgres_user.present:
    - password: password
    - require:
      - pkg: postgres-pkgs

db_sentry:
  postgres_database.present:
    - owner: pg_sentry
    - require:
      - pkg: postgres-pkgs
      - postgres_user: pg_sentry

/srv/www/sentry/sentry.conf.py:
  file.managed:
    - source: salt://sentry/sentry.conf.py
    - mode: 755

/etc/init/sentry.conf:
  file.managed:
    - source: salt://sentry/sentry.conf
    - mode: 755

sentry:
  service:
    - running
    - watch:
      - file: /srv/www/sentry/sentry.conf.py
    - require:
      - file: /etc/init/sentry.conf
      - cmd: upgrade 
 



upgrade:
  cmd:
    - name: source /srv/www/sentry/bin/activate && sentry --config=/srv/www/sentry/sentry.conf.py upgrade
    - run
  require:
    - postgres_database: db_sentry
    - file: /srv/www/sentry/sentry.conf.py
    - virtualenv : /srv/www/sentry
  watch:
    - file: /srv/www/sentry/sentry.conf.py

