import asyncio
import os
import re
import subprocess
import sys

from apps.fabric.src.client.Client import Client
from apps.fabric.src.utils.utils import write_to_log

def hand_off_item_server_global(args):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_handOffItemServerGlobal {local_peer} {local_org} {args}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

def check_condition(share_input_provider, share_prev_output_provider, share_amt, share_prev_amt):
    # share_eq_result = asyncio.run(client.req_eq(local_host, local_port, share_prev_output_provider, share_input_provider))
    # write_to_log(log_file, f"{local_port} {share_eq_result}")
    #
    # eq_result = asyncio.run(client.req_recon(local_host, local_port, share_eq_result))
    # write_to_log(log_file, f"{local_port} {eq_result}")
    #
    # if eq_result == 0:
    #     return False

    share_cmp_result = asyncio.run(client.req_cmp(local_host, local_port, share_prev_amt, share_amt, f"{item_ID}_{seq}_cmp"))
    write_to_log(log_file, f"{local_port} {share_cmp_result}")

    cmp_result = asyncio.run(client.req_recon(local_host, local_port, share_cmp_result, f"{item_ID}_{seq}_cmp_recon"))
    write_to_log(log_file, f"{local_port} {cmp_result}")

    if cmp_result > 0:
        return False

    return True

if __name__ == '__main__':
    data = re.split(' ', sys.argv[1])

    para_num = 6
    batch = len(data) // para_num

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    local_port = client.get_port(local_host)
    local_peer, local_org = client.get_peer_and_org(local_port)

    log_file = f"./apps/fabric/log/exec/log_hand_off_item_peer{local_peer}_org{local_org}.txt"

    args = ""
    for i in range(batch):
        item_ID, seq, share_input_provider, share_prev_output_provider, share_amt, share_prev_amt = data[i * para_num : (i + 1) * para_num]

        res = check_condition(share_input_provider, share_prev_output_provider, share_amt, share_prev_amt)

        args += f"{',' if i > 0 else ''}{item_ID},{seq},{'pass' if res else 'fail'}"

    if local_peer == '0' and local_org == '1':
        hand_off_item_server_global(args)