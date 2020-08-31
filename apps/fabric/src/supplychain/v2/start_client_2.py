import os
import random
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
        # print(line)
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

def create_cmp_proof(amt1, amt2, r1, r2):
    env = os.environ.copy()
    cmd = ["./apps/fabric/src/supplychain/v2/prove", str(amt1), str(amt2), str(r1), str(r2)]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "result" in line:
            list = re.split(" ", line)
            return f"{list[1]}-{list[2]}", f"{list[3]}-{list[4]}", f"{list[5]}-{list[6]}"

def register_item(registrant, amt, peer=0, org=1):
    registrant = ZR(registrant)
    C_registrant, r_registrant = Commitment().commit(registrant)

    r_amt = random.randint(0, 4294967295)

    _, _, C_amt = create_cmp_proof(amt, amt, r_amt, r_amt)

    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 2_registerItem {peer} {org} {C_registrant} {C_amt}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "payload" in line:
            item_id, seq = re.split(" ", re.split("payload:\"|\" ", line)[1])
            wait_until_shipment_committed(item_id, seq)
            return item_id, seq, r_registrant, r_amt

def hand_off_item_to_next_provider(input_provider, output_provider, amt, item_id, prev_seq, prev_amt, prev_r_provider, prev_r_amt, peer=0, org=1):
    print(f"**** input_provider {input_provider} output_provider {output_provider}")

    start_time = time.perf_counter()
    r_amt = random.randint(0, 4294967295)
    proof_amt, _, C_amt = create_cmp_proof(prev_amt, amt, prev_r_amt, r_amt)
    end_time = time.perf_counter()
    prove_amt_time = end_time - start_time

    start_time = time.perf_counter()
    input_provider = ZR(input_provider)
    output_provider = ZR(output_provider)
    C_input_provider, r_input_provider = Commitment().commit(input_provider)
    proof_provider = Commitment().prove(input_provider, prev_r_provider, r_input_provider)
    C_output_provider, r_output_provider = Commitment().commit(output_provider)
    end_time = time.perf_counter()
    prove_provider_time = end_time - start_time

    start_time = time.perf_counter()
    Commitment().check_commit(input_provider, r_input_provider, C_input_provider)
    end_time = time.perf_counter()
    check_commit_time = end_time - start_time

    start_time = time.perf_counter()
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 2_handOffItemToNextProvider {peer} {org} {C_input_provider} {C_output_provider} {C_amt} {proof_provider} {proof_amt} {item_id} {prev_seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "payload" in line:
            seq = re.split(" ", re.split("payload:\"|\" ", line)[1])[0]
            time.sleep(3)
            wait_until_shipment_committed(item_id, seq)
            end_time = time.perf_counter()
            finalize_time = end_time - start_time
            return seq, r_output_provider, r_amt, prove_provider_time, prove_amt_time, check_commit_time, finalize_time

if __name__ == '__main__':
    if os.path.exists('./time_verify.log'):
        os.remove('./time_verify.log')

    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    amt = 10
    item_id, seq, r_provider, r_amt = register_item(1, amt)
    print(f"**** item_id {item_id} seq {seq}")

    repetition = 100

    total_prove_provider_time, total_prove_amt_time, total_check_commit_time, total_finalize_time = 0, 0, 0, 0

    for i in range(1, repetition + 1):
        prev_amt = amt
        amt = prev_amt
        seq, r_provider, r_amt, prove_provider_time, prove_amt_time, check_commit_time, finalize_time = hand_off_item_to_next_provider(i, i + 1, amt, item_id, seq, prev_amt, r_provider, r_amt)
        print(f"**** item_id {item_id} seq {seq} prove_provider_time {prove_provider_time} prove_amt_time {prove_amt_time} check_commit_time {check_commit_time} finalize_time {finalize_time}")
        total_prove_provider_time += prove_provider_time
        total_prove_amt_time += prove_amt_time
        total_check_commit_time += check_commit_time
        total_finalize_time += finalize_time

    print(f"**** avg_prove_provider_time {1. * total_prove_provider_time / repetition}")
    print(f"**** ave_prove_amt_time {1. * total_prove_amt_time / repetition}")
    print(f"**** avg_check_commit_time {1. * total_check_commit_time / repetition}")
    print(f"**** avg_finalize_time {1. * total_finalize_time / repetition}")