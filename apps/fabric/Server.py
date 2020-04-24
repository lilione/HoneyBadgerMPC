import asyncio
import logging
import time

from aiohttp import web
from honeybadgermpc.elliptic_curve import Subgroup
from honeybadgermpc.field import GF
from honeybadgermpc.offline_randousha import randousha
from honeybadgermpc.utils.misc import wrap_send, subscribe_recv

field = GF(Subgroup.BLS12_381)

class Server:
    def __init__(self, n, t, myid, send, recv, http_host, http_port):
        self.n = n
        self.t = t
        self.myid = myid
        self._subscribe_task, subscribe = subscribe_recv(recv)
        def get_send_recv(tag):
            return wrap_send(tag, send), subscribe(tag)
        self.get_send_recv = get_send_recv
        self.http_host = http_host
        self.http_port = http_port
        self.inputmasks = []
        self.used_inputmasks = 0

    async def gen_inputmasks(self):
        k = 1
        target = 10
        preproc_round = 0
        while True:
            while True:
                if len(self.inputmasks) - self.used_inputmasks <= target:
                    break
                await asyncio.sleep(50)

            # Run Randousha
            logging.info(
                f"[{self.myid}] len(inputmasks): {len(self.inputmasks)} \
                used_inputmasks: {self.used_inputmasks} \
                target: {target} Initiating Randousha {k * (self.n - 2 * self.t)}"
            )
            send, recv = self.get_send_recv(f"preproc:inputmasks {preproc_round}")
            # start_time = time.time()
            rs_t, rs_2t = zip(*await randousha(self.n, self.t, k, self.myid, send, recv, field))
            assert len(rs_t) == len(rs_2t) == k * (self.n - 2 * self.t)

            # Note: here we just discard the rs_2t
            # In principle both sides of randousha could be used with
            # a small modification to randousha
            end_time = time.time()
            # logging.info(f"[{self.myid}] Randousha finished in {end_time-start_time}")
            # logging.info(f"len(rs_t): {len(rs_t)}")
            # logging.info(f"rs_t: {rs_t}")
            self.inputmasks += rs_t
            # logging.info(f"inputmasks: {inputmasks}")


            preproc_round += 1

    async def client_req_inputmask(self):
        routes = web.RouteTableDef()

        @routes.get("/inputmasks/{mask_idx}")
        async def _handler(request):
            mask_idx = int(request.match_info.get("mask_idx"))
            data = {
                "inputmask": self.inputmasks[mask_idx],
                "server_id": self.myid,
                "server_port": self.http_port,
            }
            return web.json_response(data)

        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.http_host, port=self.http_port)
        await site.start()
        logging.info(f"======= Serving on http://{self.http_host}:{self.http_port}/ ======")
        # pause here for very long time by serving HTTP requests and
        # waiting for keyboard interruption
        await asyncio.sleep(100 * 3600)