import asyncio
import os
import subprocess
import sys

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

async def check_condition():
    inputmask_share = await client.req_local_mask_share(local_host, idx_load_time)
    share_load_time = field(masked_load_time - inputmask_share)

    inputmask_share = await client.req_local_mask_share(local_host, idx_unload_time)
    share_unload_time = field(masked_unload_time - inputmask_share)

    share_cmp_result = await client.req_cmp(local_host, share_unload_time, share_load_time)
    cmp_result = await client.req_start_reconstrct(local_host, share_cmp_result)
    if cmp_result > 0:
        return False

    return True

def record_shipment_finalize_global(peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_recordShipmentFinalizeGlobal {peer} {org} {truck_ID} {idx_load_time} {idx_unload_time}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

def record_shipment_finalize_local(peer, org):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_recordShipmentFinalizeLocal {peer} {org} {idx_load_time} {masked_load_time} {idx_unload_time} {masked_unload_time}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

if __name__ == '__main__':
    truck_ID = sys.argv[1]
    idx_load_time = sys.argv[2]
    masked_load_time = int(sys.argv[3])
    idx_unload_time = sys.argv[4]
    masked_unload_time = int(sys.argv[5])

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    print('local_host', local_host)

    local_port = client.get_port(local_host)
    print("port", local_port)

    local_peer, local_org = client.get_peer_and_org(local_port)
    print('peer', local_peer)
    print('org', local_org)

    if asyncio.run(check_condition()):
        record_shipment_finalize_global()
        record_shipment_finalize_local(local_peer, local_org)


