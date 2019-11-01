# -*- coding: utf-8 -*-
import aiohttp
import asyncio
from bfxapi import Client
import copy
import json
import logging
import sys
from time import sleep, time
import threading
import types

log = logging.getLogger('scheduler')

failover_wait_sec_for_websocket_connection = 10
min_duration_sec_for_report = 1

# off websocket's debug-logging
websocketLogger = logging.getLogger('websockets')
websocketLogger.setLevel(logging.INFO)
websocketLogger.addHandler(logging.StreamHandler())

sys.path.append('bfxapi')

listTrades = []
keepingBooksBids = []
keepingBooksAsks = []
lockTrades = threading.Lock()
lockBooks = threading.Lock()

bfx = Client(
    # logLevel='DEBUG',
    logLevel='INFO',
    # Verifies that the local orderbook is up to date
    # with the bitfinex servers
    manageOrderBooks=True,
    )

@bfx.ws.on('error')
def log_error(err):
    log.error("Error: {}".format(err))

@bfx.ws.on('order_book_snapshot')
def log_snapshot(data):
    pass
    # log.debug("Initial book: {}".format(data))
    # with lockBooks:
    #     listBooks.append(data['data'])

@bfx.ws.on('order_book_update')
def log_update(data):
    # log.debug("Book update: {}".format(data))
    # with lockBooks:
    #     listBooks.append(data['data'])
    with lockBooks:
        global keepingBooksBids
        keepingBooksBids = bfx.ws.orderBooks[data['symbol']].get_bids()[:]
        global keepingBooksAsks
        keepingBooksAsks = bfx.ws.orderBooks[data['symbol']].get_asks()[:]

@bfx.ws.on('new_trade')
def log_trade(trade):
    log.debug("New trade: {}".format(trade))
    with lockTrades:
        listTrades.append(trade)

@bfx.ws.on('subscribed')
def log_subscribed(subscribed):

    if subscribed.channel_name is 'trades':
        log.debug('src(trades) msg:{}'.format(subscribed._ws.messages))
        jo = json.loads(subscribed._ws.messages[0])

        global listTrades
        tradesCopy = []

        for ent in jo[1]:
            tradesCopy.append({'mts': ent[1], 'price': ent[3], 'amount': ent[2]})

        lockTrades.acquire()
        listTrades.extend(tradesCopy)
        print(listTrades)
        lockTrades.release()

    # elif subscribed.channel_name is 'book':
    #     log.debug('src(book) msg:{}'.format(subscribed._ws.messages))
    #     jo = json.loads(subscribed._ws.messages[0])
    #     # lockBooks.acquire()
    #     # listBooks.extend(jo[1])
    #     # lockBooks.release()


class BfxClientWs:
    def __init__(self, urlTrades, urlBooks):
        self.processStart()
        self._urlTrades = urlTrades
        self._urlBooks = urlBooks

    def processStart(self):
        self._taskStop = False

        t = threading.Thread(target=self.process_ws, name='book_ws', args=[])
        t.setDaemon(False)
        t.start()

        t2 = threading.Thread(target=self.process_report, name='book_report', args=[])
        t2.setDaemon(False)
        t2.start()
       
    def process_ws(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        
        bfx.ws.on('connected', self.connected)
        bfx.ws.on('closed', self.closed)
        bfx.ws.on('disconnected', self.disconnected)

        while True:
            # If there are no problems, the blocking state is maintained on 'bfx.ws.run()'.
            bfx.ws.run()
            sleep(failover_wait_sec_for_websocket_connection)

    
    @types.coroutine
    def _taskWait(self, sec):
        yield from asyncio.sleep(sec)

    async def _syncWait(self, sec):
        await self._taskWait(sec)
        
    async def run_report(self):
        await self._reportTrades()
        await self._reportOrderbook()
        await self._syncWait(min_duration_sec_for_report)

    def process_report(self):
        asyncio.set_event_loop(asyncio.new_event_loop())

        while True:
            # print('process loop')
            t = asyncio.ensure_future(self.run_report())
            asyncio.get_event_loop().run_until_complete(t)
        
        asyncio.get_event_loop().close()

    async def connected(self):
        await bfx.ws.subscribe('book', 'tBTCUSD')
        # bfx.ws.subscribe('book', 'tETHUSD')
        await bfx.ws.subscribe('trades', 'tBTCUSD')

    def closed(self):
        print('closed')

    def disconnected(self):
        print('disconnected')

    @staticmethod
    def emptyOut(listSrc:list, lockObj):
        lockObj.acquire()
        if 0 >= len(listSrc):
            lockObj.release()
            return []
        else:
            listCopy = listSrc[:]
            del listSrc[:]
            lockObj.release()
            return listCopy

    @staticmethod
    def bidsAsks(bids:list, asks:list, lockObj):
        lockObj.acquire()
        if 0 >= len(bids):
            bidsCopy = []
        else:
            bidsCopy = bids[:]

        if 0 >= len(asks):
            asksCopy = []
        else:
            asksCopy = asks[:]
        
        lockObj.release()
        return (bidsCopy, asksCopy)

    async def _reportOrderbook(self):
        global keepingBooksBids
        global keepingBooksAsks
        listBooksTup = self.bidsAsks(keepingBooksBids, keepingBooksAsks, lockBooks)
        if 0 >= len(listBooksTup[0]) and 0 >= len(listBooksTup[1]):
            return await self._syncWait(0)

        sendData = {
            'exchange': 'bitfinex',
            'mts': int(round(time() * 1000)),
            'bids':listBooksTup[0],
            'asks':listBooksTup[1]
        }
        return await self._reportData(self._urlBooks, sendData)

    async def _reportTrades(self):
        listTradesCopy = self.emptyOut(listTrades, lockTrades)
        if 0 >= len(listTradesCopy):
            return await self._syncWait(0)
        
        sendData = {
            'exchange': 'bitfinex',
            'trades':listTradesCopy
        }
        return await self._reportData(self._urlTrades, sendData)

    async def _reportData(self, url, data, params=""):
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