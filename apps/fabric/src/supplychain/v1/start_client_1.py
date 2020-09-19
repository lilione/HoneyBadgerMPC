import asyncio
import json
import os
import re
import subprocess
import time

from apps.fabric.src.client.Client import Client
from apps.fabric.src.supplychain.v1.source_item import wait_until_inquiry_committed
from apps.fabric.src.utils.utils import get_inputmask_idx
from apps.fabric.src.utils.utils import del_file

def query_shipment(item_ID, seq, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_queryShipment {peer} {org} {item_ID} {seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        if "payload" in line:
            list = re.split("payload:\"|\" ", line)
            shipment_json = "\"" + list[1] + "\""
            shipment_str = json.loads(shipment_json)
            shipment = json.loads(shipment_str)
            return shipment

    return None

def wait_until_shipment_committed(item_ID, seq, state):
    while True:
        time.sleep(1)
        ok = True
        shipment = None
        for peer in range(2):
            for org in range(1, 3):
                shipment = query_shipment(item_ID, seq, peer, org)
                # print(peer, org, shipment)
                if shipment == None or shipment['State'] != state:
                    ok = False
                if not ok:
                    break
            if not ok:
                break
        if ok:
            print(shipment)
            return shipment

def register_item_global(args, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItemGlobal {peer} {org} {args}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" ", line)[1])

def register_item_local(args):
    env = os.environ.copy()

    tasks = []
    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_registerItemLocal {peer} {org} {args}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def register_item(batch, registrant, amt):
    para_num = 2

    inputmask_idx = get_inputmask_idx(1, batch * para_num)
    print("**** inputmask_idx", inputmask_idx)

    args = ""
    for i in range(batch):
        idx_registrant = inputmask_idx[para_num * i]
        idx_amt = inputmask_idx[para_num * i + 1]

        args += f"{',' if i > 0 else ''}{idx_registrant},{idx_amt}"
    res = register_item_global(args)
    print("**** res", res)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])

    args = ""
    for i in range(batch):
        item_ID, seq = res[i * para_num : (i + 1) * para_num]
        print(f"**** item_id {item_ID} seq {seq}")

        masked_registrant = str(registrant + mask[para_num * i])[1:-1]
        masked_amt = str(amt + mask[para_num * i + 1])[1:-1]

        wait_until_shipment_committed(item_ID, seq, "SETTLE")

        args += f"{',' if i > 0 else ''}{item_ID},{seq},{masked_registrant},{masked_amt}"

    register_item_local(args)

    return res[0::2], res[1::2]

def hand_off_item_client_global(args, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemClientGlobal {peer} {org} {args}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" ", line)[1])
        
def hand_off_item_client_local(args):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemClientLocal {peer} {org} {args}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def hand_off_item(batch, list_item_ID, list_seq, input_provider, output_provider, amt):
    para_num = 3
    inputmask_idx = get_inputmask_idx(1, batch * para_num)
    print("**** inputmask_idx", inputmask_idx)

    args = ""
    for i in range(batch):
        idx_input_provider, idx_output_provider, idx_amt = inputmask_idx[i * para_num : (i + 1) * para_num]

        args += f"{',' if i > 0 else ''}{list_item_ID[i]},{list_seq[i]},{idx_input_provider},{idx_output_provider},{idx_amt}"
    list_seq = hand_off_item_client_global(args)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])

    args = ""
    for i in range(batch):
        item_ID = list_item_ID[i]
        seq = list_seq[i]

        masked_input_provider = str(input_provider + mask[para_num * i])[1:-1]
        masked_output_provider = str(output_provider + mask[para_num * i + 1])[1:-1]
        masked_amt = str(amt + mask[para_num * i + 2])[1:-1]

        wait_until_shipment_committed(item_ID, seq, "READY")

        args += f"{',' if i > 0 else ''}{item_ID},{seq},{masked_input_provider},{masked_output_provider},{masked_amt}"

    hand_off_item_client_local(args)

    for (item_ID, seq) in zip(list_item_ID, list_seq):
        wait_until_shipment_committed(item_ID, seq, "SETTLE")
        wait_until_shipment_committed(item_ID, int(seq) - 1, "SETTLE")

    return list_seq

def source_item(item_ID, seq):
    start_time = time.perf_counter()
    env = os.environ.copy()
    tasks = []

    print("@", time.perf_counter())
    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_sourceItemStartLocal {peer} {org} {item_ID} {seq}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()
    print("@", time.perf_counter())

    wait_until_inquiry_committed(item_ID, seq, "finalizeGlobal")
    print("@", time.perf_counter())
    end_time = time.perf_counter()
    return end_time - start_time

def del_file(f):
    if os.path.exists(f):
        os.remove(f)

if __name__ == '__main__':
    del_file('./log.txt')
    del_file('./error.txt')

    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    batch = 2
    amt = 1
    list_item_ID, list_seq = register_item(batch, 1, amt)

    repetition = 2

    for i in range(1, repetition + 1):
        seq = hand_off_item(batch, list_item_ID, list_seq, i, i+1, amt)

    # source_item(item_id, seq)

