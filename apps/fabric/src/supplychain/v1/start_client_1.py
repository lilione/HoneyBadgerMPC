import asyncio
import os
import re
import subprocess

from apps.fabric.src.client.Client import Client
from apps.fabric.src.supplychain.v1.hand_off_item import wait_until_shipment_committed
from apps.fabric.src.supplychain.v1.source_item import wait_until_inquiry_committed

def get_inputmask_idx(num, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_getInputmaskIdx {peer} {org} {num}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" ", line)[1])

def register_item_global(idx_registrant, idx_amt, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItemFinalizeGlobal {peer} {org} {idx_registrant} {idx_amt}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" ", line)[1])

def register_item_local(item_ID, seq, masked_registrant, masked_amt):
    env = os.environ.copy()

    tasks = []
    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItemFinalizeLocal {peer} {org} {item_ID} {seq} {masked_registrant} {masked_amt}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def register_item(registrant, amt):
    inputmask_idx = get_inputmask_idx(2)
    print("**** inputmask_idx", inputmask_idx)

    idx_registrant = inputmask_idx[0]
    idx_amt = inputmask_idx[1]
    item_ID, seq = register_item_global(idx_registrant, idx_amt)
    print(f"**** item_ID {item_ID} seq {seq}")

    wait_until_shipment_committed(item_ID, seq, "finalizeGlobal")

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_registrant = str(registrant + mask[0])[1:-1]
    masked_amt = str(amt + mask[1])[1:-1]
    register_item_local(item_ID, seq, masked_registrant, masked_amt)

    wait_until_shipment_committed(item_ID, seq, "finalizeLocal")

    return item_ID, seq

def hand_off_item_start_global(item_ID, prev_seq, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemStartGlobal {peer} {org} {item_ID} {prev_seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split("payload:\"|\" ", line)[1]
        
def hand_off_item_start_local(idx_input_provider, masked_input_provider, idx_output_provider, masked_output_provider, idx_amt, masked_amt, item_ID, prev_seq, seq):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemStartLocal {peer} {org} {idx_input_provider} {masked_input_provider} {idx_output_provider} {masked_output_provider} {idx_amt} {masked_amt} {item_ID} {prev_seq} {seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def hand_off_item(input_provider, output_provider, amt, item_ID, prev_seq):
    inputmask_idx = get_inputmask_idx(3)
    print("**** inputmask_idx", inputmask_idx)
    
    seq = hand_off_item_start_global(item_ID, prev_seq)
    print("**** seq", seq)

    wait_until_shipment_committed(item_ID, seq, "startGlobal")

    idx_input_provider = inputmask_idx[0]
    idx_output_provider = inputmask_idx[1]
    idx_amt = inputmask_idx[2]
    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_input_provider = str(input_provider + mask[0])[1:-1]
    masked_output_provider = str(output_provider + mask[1])[1:-1]
    masked_amt = str(amt + mask[2])[1:-1]
    hand_off_item_start_local(idx_input_provider, masked_input_provider, idx_output_provider, masked_output_provider, idx_amt, masked_amt, item_ID, prev_seq, seq)

    wait_until_shipment_committed(item_ID, seq, "finalizeLocal")
    wait_until_shipment_committed(item_ID, prev_seq, "finalizeLocal")

    return seq

def source_item(item_ID, seq):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_sourceItemStartLocal {peer} {org} {item_ID} {seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    wait_until_inquiry_committed(item_ID, seq, "finalizeGlobal")

if __name__ == '__main__':
    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    item_ID, seq = register_item(1, 10)
    #
    # seq = hand_off_item(1, 2, 10, item_ID, seq)
    #
    # seq = hand_off_item(2, 3, 4, item_ID, seq)
    #
    source_item(item_ID, seq)


