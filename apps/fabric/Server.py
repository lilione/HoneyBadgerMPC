import logging
import time
import leveldb
import json

from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF
from honeybadgermpc.offline_randousha import randousha
from honeybadgermpc.utils.misc import wrap_send, subscribe_recv

field = GF(Subgroup.BLS12_381)

class Server:
    def __init__(self, myid, send, recv, http_host, http_port):
        self.myid = myid
        # self._inputmasks = []
        # self.used_inputmasks = 0
        self._subscribe_task, subscribe = subscribe_recv(recv)
        def _get_send_recv(tag):
            return wrap_send(tag, send), subscribe(tag)
        self.get_send_recv = _get_send_recv
        self.http_host = http_host
        self.http_port = http_port

    async def offline_inputmasks(self, n, t):
        db_dir = f"apps/fabric/test/data/{self.myid}"
        db = leveldb.LevelDB(db_dir)
        
        inputmasks = []
        try:
            inputmasks = json.loads(db.Get(b"inputmasks"))
        except KeyError:
            pass
        
        used_inputmasks = 0
        try:
            used_inputmasks = int(db.Get(b"used_inputmasks").decode())
        except KeyError:
            pass
        print(inputmasks, used_inputmasks)
        print(type(inputmasks), type(used_inputmasks))

        k = 1
        target = 10
        # print(inputmasks[0])
        # print(len(inputmasks) - used_inputmasks, target)
        if len(inputmasks) - used_inputmasks <= target:
            # Run Randousha
            logging.info(
                f"[{self.myid}] len(inputmasks): {len(inputmasks)} \
                used_inputmasks: {used_inputmasks} \
                target: {target} Initiating Randousha {k * (n - 2 * t)}"
            )
            send, recv = self.get_send_recv(f"preproc:inputmasks")
            start_time = time.time()
            rs_t, rs_2t = zip(*await randousha(n, t, k, self.myid, send, recv, field))
            assert len(rs_t) == len(rs_2t) == k * (n - 2 * t)

            # Note: here we just discard the rs_2t
            # In principle both sides of randousha could be used with
            # a small modification to randousha
            end_time = time.time()
            logging.info(f"[{self.myid}] Randousha finished in {end_time-start_time}")
            logging.info(f"len(rs_t): {len(rs_t)}")
            logging.info(f"rs_t: {rs_t}")
            inputmasks += rs_t
            logging.info(f"inputmasks: {inputmasks}")

            db.Put(b"inputmasks", json.dumps(inputmasks).encode())
            db.Put(b"used_inputmasks", str(used_inputmasks).encode())