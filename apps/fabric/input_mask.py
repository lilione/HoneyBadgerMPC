

async def run_client():
    pass

async def run_server(n, t, node_id, ):
    pass

def load_config(path):
    from configparser import ConfigParser

    cfgparser = ConfigParser()

    with open(path) as file_object:
        cfgparser.read_file(file_object)

    config = {
        'peers': dict(cfgparser.items('peers')),
    }

    return config

if __name__ == "__main__":
    import sys
    from honeybadgermpc.config import NodeDetails

    n = 4
    t = 1

    node_id = int(sys.argv[1])
    config_file = sys.argv[2]
    print(node_id, n)
    print(config_file)
    if node_id == n:
        value = int(sys.argv[3])

    config_dict = load_config(config_file)
    network_info = {
        int(peer_id): NodeDetails(addr_info.split(':')[0], int(addr_info.split(':')[1]))
        for peer_id, addr_info in config_dict['peers'].items()
    }

