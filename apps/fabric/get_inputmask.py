import asyncio
import os
import re
import subprocess
import toml

from apps.fabric.Client import Client

def get_inputmask_idx():
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', 'export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh getInputmaskIdx 0 1']
    task = subprocess.Popen(cmd, env=env)
    task.wait()

    file = open("apps/fabric/chaincode-log/log.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return int(re.split("payload:\"|\" \n", line)[1])

def get_inputmask(config_file, inputmask_idx):
    print("get inputmask")
    config = toml.load(config_file)

    n = config['n']
    t = config['t']

    servers = config["servers"]
    for server in servers:
        print(server)

    client = Client(n, t, servers)
    mask = asyncio.run(client.get_inputmask(inputmask_idx))
    print(f"request idx {inputmask_idx} mask {mask}")

if __name__ == '__main__':
    inputmask_idx = get_inputmask_idx()
    mask = get_inputmask("apps/fabric/conf/config.toml", inputmask_idx)