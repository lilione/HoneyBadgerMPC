from apps.fabric.src.client.Client import Client
from apps.fabric.src.utils.utils import get_inputmask_idx

if __name__ == '__main__':
    client = Client.from_toml_config("apps/fabric/conf/config.toml")

    for i in range(3):
        inputmask_idx = get_inputmask_idx(1, 2)
        print(inputmask_idx)