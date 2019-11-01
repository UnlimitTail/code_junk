# -*- coding: utf-8 -*-
import aiohttp
import asyncio
from bfxapi import Client
import json
import logging
import sys
from time import sleep, time
import threading
import types

log = logging.getLogger('scheduler')

sys.path.append('bfxapi')

class BfxClient:
    def __init__(self, url4report, API_KEY, API_SECRET, start=0, end=10, limit='100', sort=-1):

        self._bfx = Client(
            logLevel='DEBUG',
            API_KEY=API_KEY,
            API_SECRET=API_SECRET
            )
        self._url4report = url4report

        self._taskStop = False

        now = int(round(time() * 1000))
        self._then = now - (1000 * 60 * 60 * 24 * end) # (end) days ago

        self.start()

    def start(self):
        
        t = threading.Thread(target=self.process_job, args=[])
        # setDaemon=False to stop the thread after complete
        t.setDaemon(False)
        # starting the thread
        t.start()

    async def run(self):
        await self.log_historical_trades()
        await self.log_books()
        await self.syncWait()
        
    def process_job(self):
        asyncio.set_event_loop(asyncio.new_event_loop())

        while True:
            if self._taskStop is True:
                break

            t = asyncio.ensure_future(self.run())
            asyncio.get_event_loop().run_until_complete(t)

            #self.reportToDataSvc()
        
        asyncio.get_event_loop().close()

    
    async def log_historical_trades(self):
        trades = await self._bfx.rest.get_public_trades('tBTCUSD', 0, self._then)
        print ("Trades:")
        [ print (t) for t in trades ]

    async def log_books(self):
        orders = await self._bfx.rest.get_public_books('tBTCUSD')
        print ("Order book:")
        [ print (o) for o in orders ]


    @types.coroutine
    def taskSleep(self):
        yield from asyncio.sleep(1)

    async def syncWait(self):
        await self.taskSleep()


    async def reportToDataSvc(self, endpoint, data={}, params=""):
        """
        @return response
        """
        # url = '{}/{}'.format(self.host, endpoint)
        # sData = json.dumps(data)
        # headers = generate_auth_headers(
        #     self.API_KEY, self.API_SECRET, endpoint, sData)
        # headers["content-type"] = "application/json"

        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url + params, headers=headers, data=sData) as resp:
        #         text = await resp.text()
        #         if resp.status is not 200:
        #             raise Exception('POST {} failed with status {} - {}'
        #                             .format(url, resp.status, text))
        #         return await resp.json()



        url = '{}/{}'.format('self.host', endpoint)
        sData = json.dumps(data)
        headers = {
            "content-type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url + params, headers=headers, data=sData) as resp:
                text = await resp.text()
                if resp.status is not 200:
                    raise Exception('POST {} failed with status {} - {}'
                                    .format(url, resp.status, text))
                return await resp.json()