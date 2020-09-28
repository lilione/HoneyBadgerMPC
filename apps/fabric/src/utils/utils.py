import os
import re
import shutil
import subprocess

def clear_dir(dir):
    try:
        shutil.rmtree(dir)
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))

    if not os.path.exists(dir):
        os.makedirs(dir)

def write_to_log(file, s):
    with open(file, 'a') as file:
        file.write(f"{s}\n")

def get_inputmask_idxes(version, num, peer=0, org=1):
    env = os.environ.copy()
    cmd = ['docker', 'exec', 'cli', '/bin/bash', '-c', f"export CHANNEL_NAME=mychannel && bash scripts/run_cmd.sh {version}_getInputmaskIdx {peer} {org} {num}"]
    task = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    task.wait()

    stdout, stderr = task.communicate()
    for line in stdout.split(b'\n'):
        line = line.decode("utf-8")
        print(line)
        if "payload" in line:
            return re.split(" ", re.split("payload:\"|\" ", line)[1])