pkgs:
  pkg.installed:
    - pkgs:
      - mosh
      - vim
      - zsh
      - tmux
      - python-pip
      - git

satshabad:
  user.present:
    - home: /home/satshabad
    - shell: zsh
    - fullname: Satshabad Khalsa
