import asyncio
import os
import re
import subprocess
import time

from apps.fabric.src.client.Client import Client
from apps.fabric.src.supplychain.v1.hand_off_item import wait_until_shipment_committed
from apps.fabric.src.supplychain.v1.source_item import wait_until_inquiry_committed
from apps.fabric.src.utils.utils import get_inputmask_idx

def register_item_global(idx_registrant, idx_amt, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItemFinalizeGlobal {peer} {org} {idx_registrant} {idx_amt}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
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
    inputmask_idx = get_inputmask_idx(1, 2)
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
    start_time = time.perf_counter()
    inputmask_idx = get_inputmask_idx(1, 3)
    end_time = time.perf_counter()
    time_get_inputmask_idx = end_time - start_time
    print("**** inputmask_idx", inputmask_idx)

    start_time = time.perf_counter()
    seq = hand_off_item_start_global(item_ID, prev_seq)
    wait_until_shipment_committed(item_ID, seq, "startGlobal")
    end_time = time.perf_counter()
    time_get_seq = end_time - start_time
    print("**** seq", seq)

    start_time = time.perf_counter()
    idx_input_provider = inputmask_idx[0]
    idx_output_provider = inputmask_idx[1]
    idx_amt = inputmask_idx[2]
    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_input_provider = str(input_provider + mask[0])[1:-1]
    masked_output_provider = str(output_provider + mask[1])[1:-1]
    masked_amt = str(amt + mask[2])[1:-1]
    end_time = time.perf_counter()
    time_calc_inputmask = end_time - start_time

    start_time = time.perf_counter()
    hand_off_item_start_local(idx_input_provider, masked_input_provider, idx_output_provider, masked_output_provider, idx_amt, masked_amt, item_ID, prev_seq, seq)
    wait_until_shipment_committed(item_ID, seq, "finalizeLocal")
    end_time = time.perf_counter()
    time_finalized = end_time - start_time
    wait_until_shipment_committed(item_ID, prev_seq, "finalizeLocal")

    return seq, time_get_inputmask_idx, time_get_seq, time_calc_inputmask, time_finalized

def hand_off_item_start_global(item_ID, prev_seq, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemStartGlobal {peer} {org} {item_ID} {prev_seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "payload" in line:
            return re.split("payload:\"|\" ", line)[1]

def source_item(item_ID, seq):
    start_time = time.perf_counter()
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
    end_time = time.perf_counter()
    return end_time - start_time

if __name__ == '__main__':
    if os.path.exists('./time_hand_off_item.log'):
        os.remove('./time_hand_off_item.log')

    if os.path.exists('./time_source_item.log'):
        os.remove('./time_source_item.log')

    if os.path.exists('./log.txt'):
        os.remove('./log.txt')

    if os.path.exists('./error.txt'):
        os.remove('./error.txt')

    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    amt = 10
    item_id, seq = register_item(1, amt)
    print(f"**** item_id {item_id} seq {seq}")

    repetition = 100

    total_time_get_inputmask_idx, total_time_get_seq, total_time_calc_inputmask, total_time_finalized = 0, 0, 0, 0

    for i in range(1, repetition + 1):
        time.sleep(5)
        seq, time_get_inputmask_idx, time_get_seq, time_calc_inputmask, time_finalized = hand_off_item(i, i+1, amt, item_id, seq)
        total_time_get_inputmask_idx += time_get_inputmask_idx
        total_time_get_seq += time_get_seq
        total_time_calc_inputmask += time_calc_inputmask
        total_time_finalized += time_finalized
        print(f"**** item_id {item_id} seq {seq} time_get_inputmask_idx {time_get_inputmask_idx} time_get_seq {time_get_seq} time_calc_inputmask {time_calc_inputmask} time_finalized {time_finalized}")

    time_source = source_item(item_id, seq)

    print(f"**** avg_time_get_inputmask_idx {1. * total_time_get_inputmask_idx / repetition}")
    print(f"**** avg_time_get_seq {1. * total_time_get_seq / repetition}")
    print(f"**** avg_time_calc_inputmask {1. * total_time_calc_inputmask / repetition}")
    print(f"**** avg_time_finalized {1. * total_time_finalized / repetition}")
    print(f"**** avg_time_source {1. * time_source / repetition}")

