import os
import sys
from fabric import (
    task,
    Connection,
    Config,
)
from groupsudo import ThreadingGroupSudo


yaml_template = """
hosts:
  - 127.0.0.1
  - localhost
cfg_override:
  sudo:
    password: 'myRemotePasswdIsInsecure123'
connect_kwargs:
  passphrase: 'mySSHPassphraseIsInsecure123'
log: ./save-output.log
commands:
  run:
    id;
  sudo:
    id;
"""


def _save_log(filename, typeof, results):
    with open(filename, 'a') as log:
        for connection, result in results.items():
            log.write("[{0}] {1.host}: {2.stdout}".format(
                typeof, connection, result
            ))
        log.close()


@task
def create_yaml(c):
    if not os.path.isfile("./fabric.yaml"):
        with open("fabric.yaml", "w") as cfg:
            cfg.write(yaml_template)
        cfg.close()
    else:
        print("[ERR] fabric.yaml already exists!")
        sys.exit(1)


@task
def main(c):
    has_key = lambda k, c: k in list(c.keys())
    if not has_key('hosts', c) and not c.hosts:
        return

    log = None
    if has_key('log', c):
        log = c.log

    grp = ThreadingGroupSudo(
        *c.hosts,
        config=Config(overrides=c.cfg_override),
        connect_kwargs=c.connect_kwargs
    )

    if has_key('commands', c):
        if has_key('run', c.commands):
            run_res = grp.run(c.commands.run)
            if log:
                _save_log(log, 'RUN', run_res)

        if has_key('sudo', c.commands):
            sudo_res = grp.sudo(c.commands.sudo)
            if log:
                _save_log(log, 'SUDO', sudo_res)
