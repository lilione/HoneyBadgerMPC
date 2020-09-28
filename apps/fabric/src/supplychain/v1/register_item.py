import asyncio
import leveldb
import re
import sys

from apps.fabric.src.client.Client import Client
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF

field = GF(Subgroup.BLS12_381)

if __name__ == '__main__':
    db = leveldb.LevelDB('/opt/db')

    data = re.split(' ', sys.argv[1])

    para_num = 4
    batch = len(data) // para_num

    client = Client.from_toml_config('apps/fabric/conf/config.toml')

    local_host = client.get_local_host()
    local_port = client.get_port(local_host)
    local_peer, local_org = client.get_peer_and_org(local_port)

    log_file = f"./apps/fabric/log/exec/log_calc_share_peer{local_peer}_org{local_org}.txt"

    for i in range(batch):
        idx_registrant, masked_registrant, idx_amt, masked_amt = data[i * para_num : (i + 1) * para_num]

        inputmasks = asyncio.run(client.req_inputmask_shares(local_host, local_port, f"{idx_registrant},{idx_amt}"))
        share_registrant = field(int(masked_registrant) - int(inputmasks[0]))
        share_amt = field(int(masked_amt) - int(inputmasks[1]))

        db.Put(str.encode(idx_registrant), str.encode(f"{share_registrant}"))
        db.Put(str.encode(idx_amt), str.encode(f"{share_amt}"))