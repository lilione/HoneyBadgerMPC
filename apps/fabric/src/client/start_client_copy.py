import asyncio
import os
import random
import re
import subprocess
import toml

from apps.fabric.src.client.Client import Client

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

def get_inputmask_idx():
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', 'export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh getInputmaskIdx 0 1']
    task = subprocess.Popen(cmd, env=env)
    task.wait()

    file = open("apps/fabric/log/chaincode/getInputmaskIdx_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return int(re.split("payload:\"|\" \n", line)[1])

def send_masked_input(inputmask_idx, masked_input):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh sendMaskedInput {peer} {org} {inputmask_idx} {masked_input}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()


def reconstruct(inputmask_idx):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh reconstruct {peer} {org} {inputmask_idx}"]
            print(cmd)
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

if __name__ == '__main__':
    inputmask_idx = get_inputmask_idx()
    print("**** inputmask_idx", inputmask_idx)
    # inputmask_idx = 0

    client = create_client("apps/fabric/conf/config.toml")

    mask, shares = asyncio.run(client.get_inputmask(inputmask_idx))
    print(f"**** request idx {inputmask_idx} mask {mask}")

    input = random.randint(1, 10)
    print("*** input", input)
    masked_input = input + mask
    print("**** masked_input", masked_input)
    send_masked_input(inputmask_idx, str(masked_input)[1:-1])

    reconstruct(inputmask_idx)

    # asyncio.run(client.start_reconstruction(masked_input, shares))
    #
    # masked_input = 3 + mask
    # asyncio.run(client.start_reconstruction(masked_input, shares))
