import os
import re
import subprocess
import time

from apps.fabric.src.utils.commitment import Commitment
from honeybadgermpc.betterpairing import ZR
from apps.fabric.src.client.Client import Client

def query_shipment(item_ID, seq, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 2_queryShipment {peer} {org} {item_ID} {seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            list = re.split("payload:\"|\" ", line)
            return len(list[1]) > 0

def wait_until_shipment_committed(item_ID, seq):
    while True:
        time.sleep(1)
        ok = True
        for peer in range(2):
            for org in range(1, 3):
                if not query_shipment(item_ID, seq, peer, org):
                    ok = False
                if not ok:
                    break
            if not ok:
                break
        if ok:
            break

def register_item(registrant, peer=0, org=1):
    registrant = ZR(registrant)
    C, r = Commitment().commit(registrant)

    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 2_registerItem {peer} {org} {C}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            item_id, seq = re.split(" ", re.split("payload:\"|\" ", line)[1])
            return item_id, seq, r

def hand_off_item_to_next_provider(input_provider, output_provider, item_id, prev_seq, prev_r, peer=0, org=1):
    print(f"**** input_provider {input_provider} output_provider {output_provider}")
    wait_until_shipment_committed(item_id, prev_seq)

    start_time = time.clock()

    input_provider = ZR(input_provider)
    output_provider = ZR(output_provider)

    commit_input_provider, cur_r = Commitment().commit(input_provider)
    proof = Commitment().prove(input_provider, prev_r, cur_r)
    commit_output_provider, r = Commitment().commit(output_provider)

    end_time = time.clock()

    prove_time = end_time - start_time

    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 2_handOffItemToNextProvider {peer} {org} {commit_input_provider} {commit_output_provider} {proof} {item_id} {prev_seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            seq = re.split(" ", re.split("payload:\"|\" ", line)[1])[0]
            time.sleep(3)
            return seq, r, prove_time

if __name__ == '__main__':
    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    item_id, seq, r = register_item(1)
    print(f"**** item_id {item_id} seq {seq}")

    repetition = 100

    total_time = 0

    for i in range(1, repetition + 1):
        seq, r, exe_time = hand_off_item_to_next_provider(i, i+1, item_id, seq, r)
        print(f"**** item_id {item_id} seq {seq} exe_time {exe_time}")
        total_time += exe_time

    print(f"**** avg_exe_time {1. * total_time / repetition}")