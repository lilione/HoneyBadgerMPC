import sys
import time

from apps.fabric.src.utils.commitment import Commitment

if __name__ == '__main__':
    C1 = sys.argv[1]
    C2 = sys.argv[2]
    proof = sys.argv[3]

    start_time = time.perf_counter()

    result = Commitment().verify(C1, C2, proof)

    end_time = time.perf_counter()

    print("exe_time", end_time - start_time)
    print("result", int(result))
