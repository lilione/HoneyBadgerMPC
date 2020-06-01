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

    a = 10000000000
    b = 10000000000
    masked_a = a + mask[0]
    masked_b = b + mask[1]
    asyncio.run(client.test_cmp(shares, 0, masked_a, 1, masked_b))
    asyncio.run(client.test_eq(shares, 0, masked_a, 1, masked_b))


