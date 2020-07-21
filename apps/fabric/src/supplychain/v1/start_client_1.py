import asyncio
import os
import re
import subprocess
import time
import toml

from apps.fabric.src.client.Client import Client
from apps.fabric.src.supplychain.v1.hand_off_item_to_next_provider import wait_until_shipment_committed

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

def get_inputmask_idx(num):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_getInputmaskIdx 0 1 {num}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

    file = open("apps/fabric/log/chaincode/getInputmaskIdx_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

def register_item(registrant, amt):
    inputmask_idx = get_inputmask_idx(2)
    print("**** inputmask_idx", inputmask_idx)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    print(f"**** request idx {inputmask_idx} mask {mask}")

    masked_registrant = registrant + mask[0]
    print("**** masked_registrant", masked_registrant)
    masked_amt = amt + mask[1]
    print("**** masked_amt", masked_amt)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItem {peer} {org} {inputmask_idx[0]} {str(masked_registrant)[1:-1]} {inputmask_idx[1]} {str(masked_amt)[1:-1]}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/registerItem_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

def hand_off_item_to_next_provider(input_provider, output_provider, amt, item_id, prev_seq):

    wait_until_shipment_committed(item_id, prev_seq, "finalized", 0, 1)

    inputmask_idx = get_inputmask_idx(3)
    print("**** inputmask_idx", inputmask_idx)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    print(f"**** request idx {inputmask_idx} mask {mask}")

    masked_input_provider = input_provider + mask[0]
    print("**** masked_input_provider", masked_input_provider)

    masked_output_provider = output_provider + mask[1]
    print("**** masked_output_provider", masked_output_provider)

    masked_amt = amt + mask[2]
    print("**** masked_amt", masked_amt)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemToNextProvider {peer} {org} {inputmask_idx[0]} {str(masked_input_provider)[1:-1]} {inputmask_idx[1]} {str(masked_output_provider)[1:-1]} {inputmask_idx[2]} {str(masked_amt)[1:-1]} {item_id} {prev_seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/handOffItemToNextProvider_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            time.sleep(3)
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])[0]

def source_item(item_id, seq):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_sourceItem {peer} {org} {item_id} {seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    item_id, seq = register_item(1, 10)
    print(f"**** item_id {item_id} seq {seq}")

    # item_id = 0
    # seq = 0
    seq = hand_off_item_to_next_provider(1, 2, 10, item_id, seq)
    print(f"**** item_id {item_id} seq {seq}")

    # item_id = 0
    # seq = 1
    seq = hand_off_item_to_next_provider(2, 3, 4, item_id, seq)
    print(f"**** item_id {item_id} seq {seq}")
    #
    # # item_id = 0
    # # seq = 2
    # source_item(item_id, seq)