import asyncio
import leveldb
import os
import re
import subprocess
import sys

from apps.fabric.src.client.Client import Client

def source_item_server_global(args, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_sourceItemServerGlobal {peer} {org} {args}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

if __name__ == '__main__':
    db = leveldb.LevelDB('/opt/db')

    data = re.split(' ', sys.argv[1])

    para_num = 3
    batch = len(data) // para_num

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    local_port = client.get_port(local_host)
    local_peer, local_org = client.get_peer_and_org(local_port)

    log_file = f"./apps/fabric/log/exec/log_source_item_peer{local_peer}_org{local_org}.txt"

    args = ""
    for i in range(batch):
        item_ID, seq, list_idx_input_provider = data[i * para_num: (i + 1) * para_num]
        seq = int(seq)

        args += f"{',' if i > 0 else ''}{item_ID},{seq},"

        list_input_provider = ''
        if len(list_idx_input_provider) > 0:
            list_idx_input_provider = re.split(',', list_idx_input_provider)
            for idx_input_provider in list_idx_input_provider:
                share_input_provider = db.Get(str.encode(idx_input_provider)).decode()
                input_provider = asyncio.run(client.req_recon(local_host, local_port, share_input_provider, f"{item_ID}_{seq}_recon"))
                list_input_provider += f"{'-' if len(list_input_provider) > 0 else ''}{input_provider}"
                seq -= 1

        args += f"{list_input_provider}"

    if local_peer == '0' and local_org == '1':
        source_item_server_global(args)
