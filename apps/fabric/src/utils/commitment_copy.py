# python3.7 apps/fabric/src/utils/commitment.py

from honeybadgermpc.betterpairing import ZR

class Commitment:
    def __init__(self):
        self.g = ZR.random(seed=2)
        self.h = ZR.random(seed=3)

    def commit(self, x):
        X = pow(self.g, x.__int__())

        r = ZR.random()
        C = pow(self.g, x.__int__()) * pow(self.h, r.__int__())

        KX, KC, sx, sr = self.create_witness(x, r)
        return C, (X, KX, KC, sx, sr)

    def create_witness(self, x, r):
        kx = ZR.random()
        KX = pow(self.g, kx.__int__())
        kc = ZR.random()
        KC = pow(self.g, kx.__int__()) * pow(self.h, kc.__int__())
        c = ZR.hash(str.encode(str(KX) + str(KC)))
        sx = kx.__int__() + x.__int__() * c.__int__()
        sr = kc.__int__() + c.__int__() * r.__int__()
        return KX, KC, sx, sr

    def verify(self, C, prf):
        (X, KX, KC, sx, sr) = prf
        assert type(KX) == type(KC) == ZR
        assert type(sx) == type(sr) == int
        c = ZR.hash(str.encode(str(KX) + str(KC)))
        return pow(self.g, sx) == KX * pow(X, c.__int__()) and pow(self.g, sx) * pow(self.h, sr) == KC * pow(C, c.__int__())

if __name__ == '__main__':
    commit = Commitment()

    x = ZR.random()
    C, prf = commit.commit(x)

    assert commit.verify(C, prf)

    # print(C, type(C))
    # C_str = C.__str__()
    # print(C_str, type(C_str))
    # C_recover = ZR(C_str)
    # print(C_recover, type(C_recover))