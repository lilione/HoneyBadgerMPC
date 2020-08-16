# python3.7 apps/fabric/src/utils/commitment.py

import re

from honeybadgermpc.betterpairing import G1, ZR

class Commitment:
    def __init__(self):
        self.g = G1.rand(seed=[2])
        self.h = G1.rand(seed=[3])

    def commit(self, x):
        r = ZR.random()
        C = pow(self.g, x) * pow(self.h, r)

        return C.__getstate__().hex(), r

    def check_commit(self, x, r, C):
        return pow(self.g, x) * pow(self.h, r) == C

    def prove(self, x, r1, r2):
        k = ZR.random()
        k1 = ZR.random()
        k2 = ZR.random()

        K1 = pow(self.g, k) * pow(self.h, k1)
        K2 = pow(self.g, k) * pow(self.h, k2)

        c = ZR.hash(str.encode(str(K1) + str(K2)))

        s = k + x * c
        s1 = k1 + r1 * c
        s2 = k2 + r2 * c

        return f"{K1.__getstate__().hex()}-{K2.__getstate__().hex()}-{s}-{s1}-{s2}"

    def verify(self, _C1, _C2, _prf):
        C1 = G1()
        C1.__setstate__(bytes.fromhex(_C1))

        C2 = G1()
        C2.__setstate__(bytes.fromhex(_C2))
        assert type(C1) == type(C2) == G1

        prf = re.split("-", _prf)

        K1 = G1()
        K1.__setstate__(bytes.fromhex(prf[0]))

        K2 = G1()
        K2.__setstate__(bytes.fromhex(prf[1]))
        assert type(K1) == type(K2) == G1

        s = ZR(prf[2])
        s1 = ZR(prf[3])
        s2 = ZR(prf[4])
        assert type(s) == type(s1) == type(s2) == ZR

        c = ZR.hash(str.encode(str(K1) + str(K2)))

        return  pow(self.g, s) * pow(self.h, s1) == K1 * pow(C1, c) \
            and pow(self.g, s) * pow(self.h, s2) == K2 * pow(C2, c)

if __name__ == '__main__':
    commit = Commitment()

    x = ZR.random()

    # y = G1.rand()
    # print("y", y)
    # b = (y.__getstate__()).hex()
    # print("b", b)
    # r = G1()
    # r.__setstate__(bytes.fromhex(b))
    # print("r", r)

    C1, r1 = commit.commit(x)
    print("C1", C1, "r1", r1)

    C2, r2 = commit.commit(x)
    print("C2", C2, "r2", r2)

    prf = commit.prove(x, r1, r2)
    print("proof", prf)

    assert commit.verify(C1, C2, prf)