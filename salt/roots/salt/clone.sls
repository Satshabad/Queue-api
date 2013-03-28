git:
  pkg:
    - installed

https://github.com/Satshabad/Queue-API.git:
  git.latest:
    - target: /home/vagrant/Queue
    - require:
      - pkg: git 
