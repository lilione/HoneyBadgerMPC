import asyncio
import json
import os
import re
import subprocess
import sys
import time

from apps.fabric.src.client.Client import Client

def query_inquiry(item_ID, seq, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_queryInquiry {peer} {org} {item_ID} {seq}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        if "payload" in line:
            list = re.split("payload:\"|\" ", line)
            inquiry_json = "\"" + list[1] + "\""
            inquiry_str = json.loads(inquiry_json)
            inquiry = json.loads(inquiry_str)
            return inquiry

    return None

def wait_until_inquiry_committed(item_ID, seq, state):
    while True:
        time.sleep(1)
        ok = True
        inquiry = None
        for peer in range(2):
            for org in range(1, 3):
                inquiry = query_inquiry(item_ID, seq, peer, org)
                print(peer, org, inquiry)
                if inquiry == None or inquiry['State'] != state:
                    ok = False
                if not ok:
                    break
            if not ok:
                break
        if ok:
            print(inquiry)
            return inquiry

def source_item_finalize_global(item_ID, seq, list_input_provider_json, peer=0, org=1):
    wait_until_inquiry_committed(item_ID, seq, "startLocal")

    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh 1_sourceItemFinalizeGlobal {peer} {org} {item_ID} {seq} {list_input_provider_json}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

if __name__ == '__main__':
    item_ID = sys.argv[1]
    seq = sys.argv[2]
    shares = sys.argv[3]

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    print('local_host', local_host)


    print(shares)
    print(len(shares))
    print(re.split(',', shares))
    list_input_provider = ''
    if len(shares) > 0:
        for share_input_provider in re.split(',', shares):
            input_provider = asyncio.run(client.req_start_reconstrct(local_host, share_input_provider))
            print('input_provider', input_provider)
            list_input_provider += str(input_provider) + ','

    list_input_provider = list_input_provider[:-1]

    source_item_finalize_global(item_ID, seq, list_input_provider)