import os
import re
import subprocess
import sys
import time

from apps.fabric.src.utils.commitment import Commitment

def verify_cmp_proof(prev_amt, suc_amt, proof_amt):
    vk, proof = re.split("-", proof_amt)
    prev = re.split("-", prev_amt)
    suc = re.split("-", suc_amt)

    env = os.environ.copy()
    cmd = ["./apps/fabric/src/supplychain/v2/verify", str(vk), str(proof), str(prev[0]), str(prev[1]), str(suc[0]), str(suc[1])]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        # print(line)
        if "Verification status: " in line:
            list = re.split("Verification status: ", line)
            return int(list[1])

if __name__ == '__main__':
    start_time = time.perf_counter()

    prev_provider = sys.argv[1]
    suc_provider = sys.argv[2]
    proof_provider = sys.argv[3]

    result = Commitment().verify(prev_provider, suc_provider, proof_provider)

    end_time = time.perf_counter()

    verify_provider_time = end_time - start_time

    start_time = time.perf_counter()

    prev_amt = sys.argv[4]
    suc_amt = sys.argv[5]
    proof_amt = sys.argv[6]

    result = result and verify_cmp_proof(prev_amt, suc_amt, proof_amt)

    end_time = time.perf_counter()

    verify_amt_time = end_time - start_time

    with open("./time_verify.log", 'a') as file:
        file.write(str(verify_provider_time) + '\t' + str(verify_amt_time) + '\n')

    print("result", int(result))


