# python3.7 apps/fabric/test/test_cmp.py

import asyncio
import toml

from apps.fabric.src.client.Client import Client

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/config.toml")

    inputmask_idx = [0, 1]

    mask, shares = [], []
    for i in inputmask_idx:
        res = asyncio.run(client.get_inputmask(int(i)))
        mask.append(res[0])
        shares.append(res[1])
    print(f"**** request idx {inputmask_idx} mask {mask} shares {shares}")

    a = 1
    b = 1
    masked_a = a + mask[0]
    masked_b = b + mask[1]
    asyncio.run(client.test_cmp(shares, 0, masked_a, 1, masked_b))
    asyncio.run(client.test_eq(shares, 0, masked_a, 1, masked_b))
    # share_a = ["37097938878058093083960687201296720559757447508863536013563526396501569141655", "23848566017774196079091266107560010204962535111902597738933034516442944771538", "6422066283921898292986580587518230003891237525535332395483261789627545055927", "43520005161979991376947267788814950563648685034398868409046788186129114197576"]
    # share_b = ["25044737675112334596360280677777300333898667971637604807076982766591735404107", "50109579031875884916389467557221464014359605686815961733266823290771688012218", "6903004965442852038070196408985251579711511917501305102372250333718865574252", "24050076198171205998649024528682210121463210140696974161321713467251721251581"]
    # asyncio.run(client.test_cmp(share_a, share_b))


