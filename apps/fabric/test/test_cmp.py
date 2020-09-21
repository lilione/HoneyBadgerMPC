# python3.7 apps/fabric/test/test_cmp.py

import asyncio
import time
import toml

from apps.fabric.src.client.Client import Client

def create_client(config_file):
    config = toml.load(config_file)

    n = config['n']
    t = config['t']
    servers = config["servers"]

    return Client(n, t, servers)

if __name__ == '__main__':
    client = create_client("apps/fabric/conf/test_config.toml")

    inputmask_idx = [0, 1]

    mask, shares = [], []
    for i in inputmask_idx:
        res = asyncio.run(client.get_inputmask(int(i)))
        mask.append(res[0])
        shares.append(res[1])

    a = 1
    b = 1
    masked_a = a + mask[0]
    masked_b = b + mask[1]

    for i in range(40):
        # t = time.perf_counter()
        # cmp_result_shares = asyncio.run(client.test_cmp(shares, 0, masked_a, 1, masked_b, f"cmp_{i}"))
        # print("cmp_result_shares", cmp_result_shares, "time", time.perf_counter() - t)
        # t = time.perf_counter()
        # res = asyncio.run(client.test_recon(cmp_result_shares, f"recon_cmp_{i}"))
        # print("cmp_result", res, "time", time.perf_counter() - t)

        t = time.perf_counter()
        eq_result_shares = asyncio.run(client.test_eq(shares, 0, masked_a, 1, masked_b, f"eq_{i}"))
        print("eq_result_shares", eq_result_shares, "time", time.perf_counter() - t)
        t = time.perf_counter()
        res = asyncio.run(client.test_recon(eq_result_shares, f"recon_eq_{i}"))
        print("eq_result", res, "time", time.perf_counter() - t)