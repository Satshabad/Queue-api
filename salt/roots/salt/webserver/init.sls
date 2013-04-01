uwsgi_pkg_reqs:
  pkg:
    - installed
    - names:
      - python-pip
      - python-dev

uwsgipip:
  pip.installed:
    - name: uwsgi
    - require:
       - pkg: uwsgi_pkg_reqs

nginx:
  pkg:
    - latest
  service:
    - running
    - watch:
      - file:  /etc/nginx/sites-available/default
      - file:  /etc/nginx/sites-enabled/default
   
/etc/nginx/sites-available/default:
  file.managed:
    - source: salt://webserver/nginx.conf
    - makedirs: True
    - mode: 755



/etc/nginx/sites-enabled/default:
  file.symlink:
    - target: /etc/nginx/sites-available/default
    - mode: 755
    - force: True
    - require:
      - file: /etc/nginx/sites-available/default

