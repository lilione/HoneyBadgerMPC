# python3.7 apps/fabric/src/utils/commitment.py

import re

from honeybadgermpc.betterpairing import ZR

class Commitment:
    def __init__(self):
        self.g = ZR.random(seed=2)
        self.h = ZR.random(seed=3)

    def commit(self, x):
        r = ZR.random()
        C = pow(self.g, x.__int__()) * pow(self.h, r.__int__())

        return C, r

    def prove(self, x, r1, r2):
        k = ZR.random()
        k1 = ZR.random()
        k2 = ZR.random()

        K1 = pow(self.g, k.__int__()) * pow(self.h, k1.__int__())
        K2 = pow(self.g, k.__int__()) * pow(self.h, k2.__int__())

        c = ZR.hash(str.encode(str(K1) + str(K2)))

        s = k.__int__() + x.__int__() * c.__int__()
        s1 = k1.__int__() + r1.__int__() * c.__int__()
        s2 = k2.__int__() + r2.__int__() * c.__int__()

        return f"{K1}-{K2}-{s}-{s1}-{s2}"

    def verify(self, C1, C2, prf):
        prf = re.split("-", prf)
        K1 = ZR(prf[0])
        K2 = ZR(prf[1])
        s = int(prf[2])
        s1 = int(prf[3])
        s2 = int(prf[4])
        assert type(K1) == type(K2) == type(C1) == type(C2) == ZR
        assert type(s) == type(s1) == type(s2) == int

        c = ZR.hash(str.encode(str(K1) + str(K2)))

        return  pow(self.g, s) * pow(self.h, s1) == K1 * pow(C1, c.__int__()) \
            and pow(self.g, s) * pow(self.h, s2) == K2 * pow(C2, c.__int__())

if __name__ == '__main__':
    commit = Commitment()

    x = ZR.random()

    C1, r1 = commit.commit(x)
    print("C1", C1, "r1", r1)

    C2, r2 = commit.commit(x)
    print("C2", C2, "r2", r2)

    prf = commit.prove(x, r1, r2)
    print("proof", prf)
    assert commit.verify(C1, C2, prf)