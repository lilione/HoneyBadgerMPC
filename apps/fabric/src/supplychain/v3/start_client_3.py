import asyncio
import os
import re
import subprocess
import time

from apps.fabric.src.client.Client import Client
from apps.fabric.src.utils.utils import get_inputmask_idx

def create_truck_global(peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_createTruckGlobal {peer} {org}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split("payload:\"|\" ", line)[1]

def record_shipment_start_local(truck_ID, idx_load_time, masked_load_time, idx_unload_time, masked_unload_time):
    env = os.environ.copy()

    tasks = []
    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_recordShipmentStartLocal {peer} {org} {truck_ID} {idx_load_time} {masked_load_time} {idx_unload_time} {masked_unload_time}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def record_shipment(truck_ID, load_time, unload_time):
    inputmask_idx = get_inputmask_idx(3, 2)
    print("**** inputmask_idx", inputmask_idx)

    idx_load_time = inputmask_idx[0]
    idx_unload_time = inputmask_idx[1]

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_load_time = str(load_time + mask[0])[1:-1]
    masked_unload_time = str(unload_time + mask[1])[1:-1]

    record_shipment_start_local(truck_ID, idx_load_time, masked_load_time, idx_unload_time, masked_unload_time)

    time.sleep(20)

def query_positions_start_local(truck_id, idx_init_time, masked_init_time, idx_end_time, masked_end_time):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_queryPositionsStartLocal {peer} {org} {truck_id} {idx_init_time} {masked_init_time} {idx_end_time} {masked_end_time}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def query_positions(truck_id, init_time, end_time):
    inputmask_idx = get_inputmask_idx(3, 2)

    idx_init_time = inputmask_idx[0]
    idx_end_time = inputmask_idx[1]

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_init_time = str(init_time + mask[0])[1:-1]
    masked_end_time = str(end_time + mask[1])[1:-1]

    query_positions_start_local(truck_id, idx_init_time, masked_init_time, idx_end_time, masked_end_time)

def query_number_start_local(truck_id, idx_init_time, masked_init_time, idx_end_time, masked_end_time):
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_queryNumberStartLocal {peer} {org} {truck_id} {idx_init_time} {masked_init_time} {idx_end_time} {masked_end_time}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

def query_number(truck_id, init_time, end_time):
    inputmask_idx = get_inputmask_idx(3, 2)

    idx_init_time = inputmask_idx[0]
    idx_end_time = inputmask_idx[1]

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])
    masked_init_time = str(init_time + mask[0])[1:-1]
    masked_end_time = str(end_time + mask[1])[1:-1]

    query_number_start_local(truck_id, idx_init_time, masked_init_time, idx_end_time, masked_end_time)

if __name__ == '__main__':
    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    truck_id = create_truck_global()
    print(f"**** truck_id {truck_id}")

    record_shipment(truck_id, 1, 3)

    record_shipment(truck_id, 2, 4)

    record_shipment(truck_id, 3, 5)

    record_shipment(truck_id, 4, 6)

    record_shipment(truck_id, 5, 7)

    query_positions(truck_id, 4, 4)

    query_number(truck_id, 4, 4)
