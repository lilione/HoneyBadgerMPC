import ast
import asyncio
import json
import os
import re
import subprocess
import sys
import time

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

def query_shipment(item_ID, seq, peer, org):
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

def wait_until_shipment_committed(item_ID, seq, state, peer, org):
    while True:
        time.sleep(1)
        shipment = query_shipment(item_ID, seq, peer, org)
        if shipment != None and shipment['State'] == state:
            return shipment

async def check_condition():
    inputmask_share = await client.req_local_mask_share(host, idx_input_provider)
    share_input_provider = field(masked_input_provider - inputmask_share)
    share_eq_result = await client.req_eq(host, share_prev_output_provider, share_input_provider)
    eq_result = await client.req_start_reconstrct(host, share_eq_result)
    if eq_result == 0:
        return False

    inputmask_share = await client.req_local_mask_share(host, idx_amt)
    share_amt = field(masked_amt - inputmask_share)
    share_cmp_result = await client.req_cmp(host, share_prev_amt, share_amt)
    cmp_result = await client.req_start_reconstrct(host, share_cmp_result)
    if cmp_result > 0:
        return False

    return True

def hand_off_item_to_next_provider_finalize():
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemToNextProviderFinalize {peer} {org} {idx_input_provider} {masked_input_provider} {idx_output_provider} {masked_output_provider} {idx_amt} {masked_amt} {item_ID} {prev_seq} {seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

if __name__ == '__main__':
    sys.stdout.flush()
    idx_input_provider = sys.argv[1]
    masked_input_provider = int(sys.argv[2])
    idx_output_provider = sys.argv[3]
    masked_output_provider = int(sys.argv[4])
    idx_amt = sys.argv[5]
    masked_amt = int(sys.argv[6])
    item_ID = sys.argv[7]
    prev_seq = sys.argv[8]
    seq = sys.argv[9]
    share_prev_output_provider = sys.argv[10]
    share_prev_amt = sys.argv[11]

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    host = client.get_local_host()
    print("host", host)

    port = client.get_port(host)
    print("port", port)

    peer, org = client.get_peer_and_org(port)
    print('peer', peer)
    print('org', org)

    shipment = wait_until_shipment_committed(item_ID, seq, "ongoing", peer, org)
    print(shipment)

    if asyncio.run(check_condition()):
        hand_off_item_to_next_provider_finalize()

        shipment = wait_until_shipment_committed(item_ID, seq, "finalized", peer, org)
        print(shipment)

        prev_shipment = query_shipment(item_ID, prev_seq, peer, org)
        print(prev_shipment)