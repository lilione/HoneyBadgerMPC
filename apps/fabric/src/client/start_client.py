import os
import re
import subprocess
import time
import toml

from apps.fabric.src.utils.commitment import Commitment
from honeybadgermpc.betterpairing import ZR


from apps.fabric.src.client.Client import Client

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

def register_item(registrant):
    registrant = ZR(registrant)

    C, r = Commitment().commit(registrant)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh registerItem {peer} {org} {C}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/registerItem_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            item_id, seq = re.split(" ", re.split("payload:\"|\" \n", line)[1])
            print(item_id, seq, r)
            return item_id, seq, r

def hand_off_item_to_next_provider(input_provider, output_provider, item_id, prev_seq, prev_r):
    input_provider = ZR(input_provider)
    output_provider = ZR(output_provider)

    commit_input_provider, cur_r = Commitment().commit(input_provider)
    proof = Commitment().prove(input_provider, prev_r, cur_r)
    print("proof", proof)

    commit_output_provider, r = Commitment().commit(output_provider)
    print(commit_input_provider, commit_output_provider)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh handOffItemToNextProvider {peer} {org} {commit_input_provider} {commit_output_provider} {proof} {item_id} {prev_seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/handOffItemToNextProvider_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            seq = re.split(" ", re.split("payload:\"|\" \n", line)[1])[0]
            time.sleep(3)
            return seq, r

# def source_item(itemID, nonce):
#     env = os.environ.copy()
#     tasks = []
#
#     for peer in range(2):
#         for org in range(1, 3):
#             cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh sourceItem {peer} {org} {itemID} {nonce}"]
#             task = subprocess.Popen(cmd, env=env)
#             tasks.append(task)
#
#     for task in tasks:
#         task.wait()

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    item_id, seq, r = register_item(1)
    print(f"**** item_id {item_id} seq {seq}")

    seq, r = hand_off_item_to_next_provider(1, 2, item_id, seq, r)
    print(f"**** item_id {item_id} seq {seq}")

    seq, r = hand_off_item_to_next_provider(2, 3, item_id, seq, r)
    print(f"**** item_id {item_id} seq {seq}")
