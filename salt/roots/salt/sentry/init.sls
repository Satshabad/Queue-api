pipinstalled:
  pkg:
    - installed
    - names:
      - python-pip

sentrypip:
  pip.installed:
    - name: sentry
  require:
    - pkg: pipinstalled
