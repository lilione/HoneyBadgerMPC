import asyncio
import sys
import time

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

def write_to_log(st):
    with open(log_file, 'a') as file:
        file.write(st + '\n')

if __name__ == '__main__':
    inputmask_idx = sys.argv[1]
    masked_input = int(sys.argv[2])

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    local_port = client.get_port(local_host)
    local_peer, local_org = client.get_peer_and_org(local_port)

    log_file = f"./log_calc_share_peer{local_peer}_org{local_org}.txt"

    write_to_log(f"start calc_share: {time.perf_counter()}")

    inputmask_share = asyncio.run(client.req_local_mask_share(local_host, inputmask_idx))

    share = field(masked_input - inputmask_share)

    write_to_log(f"end calc_share: {time.perf_counter()}")

    print("share", share)
