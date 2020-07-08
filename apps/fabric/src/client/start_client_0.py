import ast
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

def get_inputmask_idx(num):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh getInputmaskIdx 0 1 {num}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

    file = open("apps/fabric/log/chaincode/getInputmaskIdx_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

def register_item(idx_registrant, masked_registrant, idx_amt, masked_amt):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh registerItem {peer} {org} {idx_registrant} {masked_registrant} {idx_amt} {masked_amt}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/registerItem_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

def hand_off_item_to_next_provider(idxInputProvider, maskedInputProvider, idxOutputProvider, maskedOutputProvider, idxAmt, maskedAmt, itemID, prevSeq):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh handOffItemToNextProvider {peer} {org} {idxInputProvider} {maskedInputProvider} {idxOutputProvider} {maskedOutputProvider} {idxAmt} {maskedAmt} {itemID} {prevSeq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/handOffItemToNextProvider_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])[0]

def source_item(itemID, nonce):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh sourceItem {peer} {org} {itemID} {nonce}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    # inputmask_idx = get_inputmask_idx(2)
    # print("**** inputmask_idx", inputmask_idx)
    #
    # mask = []
    # for i in inputmask_idx:
    #     mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    # print(f"**** request idx {inputmask_idx} mask {mask}")
    #
    # output_provider = random.randint(1, 10)
    # print("*** output_provider", output_provider)
    # masked_output_provider = output_provider + mask[0]
    # print("**** masked_output_provider", masked_output_provider)
    #
    # amt = random.randint(1, 10)
    # print("*** amt", amt)
    # masked_amt = amt + mask[1]
    # print("**** masked_amt", masked_amt)
    #
    # item_id, seq = register_item(inputmask_idx[0], str(masked_output_provider)[1:-1], inputmask_idx[1], str(masked_amt)[1:-1])
    # print(f"**** item_id {item_id} seq {seq}")

    ###########

    # item_id = 0
    # seq = 0
    # output_provider = 6
    # amt = 7
    #
    # inputmask_idx = get_inputmask_idx(3)
    # print("**** inputmask_idx", inputmask_idx)
    #
    # mask = []
    # for i in inputmask_idx:
    #     mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    # print(f"**** request idx {inputmask_idx} mask {mask}")
    #
    # input_provider = output_provider
    # print("*** input_provider", input_provider)
    # masked_input_provider = input_provider + mask[0]
    # print("**** masked_input_provider", masked_input_provider)
    #
    # output_provider = random.randint(1, 10)
    # print("*** output_provider", output_provider)
    # masked_output_provider = output_provider + mask[1]
    # print("**** masked_output_provider", masked_output_provider)
    #
    # amt = random.randint(1, amt)
    # print("*** amt", amt)
    # masked_amt = amt + mask[2]
    # print("**** masked_amt", masked_amt)
    #
    # seq = hand_off_item_to_next_provider(inputmask_idx[0], str(masked_input_provider)[1:-1], inputmask_idx[1], str(masked_output_provider)[1:-1], inputmask_idx[2], str(masked_output_provider)[1:-1], item_id, seq)
    # print(f"**** item_id {item_id} seq {seq}")

    #############

    # item_id = 0
    # seq = 1
    # output_provider = 3
    # amt = 4
    #
    # inputmask_idx = get_inputmask_idx(3)
    # print("**** inputmask_idx", inputmask_idx)
    #
    # mask = []
    # for i in inputmask_idx:
    #     mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    # print(f"**** request idx {inputmask_idx} mask {mask}")
    #
    # input_provider = output_provider
    # print("*** input_provider", input_provider)
    # masked_input_provider = input_provider + mask[0]
    # print("**** masked_input_provider", masked_input_provider)
    #
    # output_provider = random.randint(1, 10)
    # print("*** output_provider", output_provider)
    # masked_output_provider = output_provider + mask[1]
    # print("**** masked_output_provider", masked_output_provider)
    #
    # amt = random.randint(1, amt)
    # print("*** amt", amt)
    # masked_amt = amt + mask[2]
    # print("**** masked_amt", masked_amt)
    #
    # seq = hand_off_item_to_next_provider(inputmask_idx[0], str(masked_input_provider)[1:-1], inputmask_idx[1], str(masked_output_provider)[1:-1], inputmask_idx[2], str(masked_output_provider)[1:-1], item_id, seq)
    # print(f"**** item_id {item_id} seq {seq}")

    #########

    item_id = 0
    seq = 2
    source_item(item_id, seq)