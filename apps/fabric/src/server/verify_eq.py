import sys

from apps.fabric.src.utils.commitment import Commitment
from honeybadgermpc.betterpairing import ZR

if __name__ == '__main__':
    C1 = ZR(int(sys.argv[1]))
    C2 = ZR(int(sys.argv[2]))
    proof = sys.argv[3]

    result = Commitment().verify(C1, C2, proof)

    print("result", int(result))
