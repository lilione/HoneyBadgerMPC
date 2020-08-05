import asyncio
import os
import re
import subprocess
import sys

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

def query_number_finalize_global(peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 3_queryNumberFinalizeGlobal {peer} {org} {truck_ID} {idx_init_time} {masked_init_time} {idx_end_time} {masked_end_time} {number}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

if __name__ == '__main__':
    truck_ID = sys.argv[1]
    idx_init_time = sys.argv[2]
    masked_init_time = int(sys.argv[3])
    idx_end_time = sys.argv[4]
    masked_end_time = int(sys.argv[5])
    shares = sys.argv[6]

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    print('local_host', local_host)

    local_port = client.get_port(local_host)
    print('port', local_port)

    local_peer, local_org = client.get_peer_and_org(local_port)
    print('peer', local_peer)
    print('org', local_org)

    _shares = re.split(';', shares)
    shares = []
    for share in _shares:
        shares.append(re.split(',', share))

    print(shares)

    inputmask_share = asyncio.run(client.req_local_mask_share(local_host, idx_init_time))
    share_init_time = field(masked_init_time - inputmask_share)

    inputmask_share = asyncio.run(client.req_local_mask_share(local_host, idx_end_time))
    share_end_time = field(masked_end_time - inputmask_share)

    share_number = field(0)
    for index, share in enumerate(shares):
        share_load_time = field(int(share[0][1:-1]))
        share_unload_time = field(int(share[1][1:-1]))
        print(share_load_time, share_unload_time)
        results = []
        res = asyncio.run(client.req_cmp(local_host, share_init_time, share_load_time))
        results.append(res)
        res = asyncio.run(client.req_cmp(local_host, share_unload_time, share_end_time))
        results.append(res)
        res = asyncio.run(client.req_one_minus_share(local_host, results[0]))
        results.append(res)
        res = asyncio.run(client.req_one_minus_share(local_host, results[1]))
        results.append(res)
        res = asyncio.run(client.req_mul(local_host, results[2], results[3]))
        share_number = share_number + field(int(res[1:-1]))

    number = asyncio.run(client.req_start_reconstrct(local_host, share_number))
    query_number_finalize_global()