import ast
import asyncio
import os
import random
import re
import subprocess
import toml
import time

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

def create_truck():
    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh createTruck {peer} {org}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/createTruck_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

def record_shipment(truck_id, load_time, unload_time):
    inputmask_idx = get_inputmask_idx(2)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])

    print("**** load_time", load_time)
    masked_load_time = str(load_time + mask[0])[1:-1]
    print("**** masked_load_time", masked_load_time)

    print("**** unload_time", unload_time)
    masked_unload_time = str(unload_time + mask[1])[1:-1]
    print("**** masked_unload_time", masked_unload_time)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh recordShipment {peer} {org} {truck_id} {inputmask_idx[0]} {masked_load_time} {inputmask_idx[1]} {masked_unload_time}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    time.sleep(2)

def query_positions(truck_id, init_time, end_time):
    inputmask_idx = get_inputmask_idx(2)

    mask = []
    for i in inputmask_idx:
        mask.append(asyncio.run(client.get_inputmask(int(i)))[0])

    print("**** init_time", init_time)
    masked_init_time = str(init_time + mask[0])[1:-1]
    print("**** masked_init_time", masked_init_time)

    print("**** end_time", end_time)
    masked_end_time = str(end_time + mask[1])[1:-1]
    print("**** masked_end_time", masked_end_time)

    env = os.environ.copy()
    tasks = []

    for peer in range(2):
        for org in range(1, 3):
            cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh queryPositions {peer} {org} {truck_id} {inputmask_idx[0]} {masked_init_time} {inputmask_idx[1]} {masked_end_time}"]
            task = subprocess.Popen(cmd, env=env)
            tasks.append(task)

    for task in tasks:
        task.wait()

    file = open("apps/fabric/log/chaincode/recordShipment_peer0org1.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    truck_id = create_truck()
    # truck_id = ['0']
    print(f"**** truck_id {truck_id}")

    record_shipment(str(truck_id)[1:-1], 1, 3)

    record_shipment(str(truck_id)[1:-1], 2, 4)

    record_shipment(str(truck_id)[1:-1], 3, 5)

    record_shipment(str(truck_id)[1:-1], 4, 6)

    record_shipment(str(truck_id)[1:-1], 5, 7)

    query_positions(str(truck_id)[1:-1], 4, 4)
