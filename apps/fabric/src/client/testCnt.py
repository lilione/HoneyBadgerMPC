import asyncio
import os
import re
import subprocess
import time
import toml

from apps.fabric.src.client.Client import Client

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

def testCnt(peer, org):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh testCnt {peer} {org}"]
    task = subprocess.Popen(cmd, env=env)
    task.wait()

    file = open(f"apps/fabric/log/chaincode/testCnt_peer{peer}org{org}.txt", "r")
    for line in file.readlines():
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" \n", line)[1])

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    dbCnt, ledgerCnt = testCnt(0, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)

    dbCnt, ledgerCnt = testCnt(0, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)

    dbCnt, ledgerCnt = testCnt(0, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)

    dbCnt, ledgerCnt = testCnt(0, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)

    dbCnt, ledgerCnt = testCnt(0, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)

    dbCnt, ledgerCnt = testCnt(1, 1)
    print("dbCnt", dbCnt)
    print("ledgerCnt", ledgerCnt)