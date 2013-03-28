python-pip:
  pkg.installed

queue:
  pip.installed:
    - requirements: /home/vagrant/Queue/requirements.txt
    - require:
      - pkg: python-pip
      - git: https://github.com/Satshabad/Queue-API.git 

/usr/bin/python /home/vagrant/Queue/queueapi.py:
  cmd:
    - run
    - require:
        - pip: queue
    - watch:
      - git: https://github.com/Satshabad/Queue-API.git 
