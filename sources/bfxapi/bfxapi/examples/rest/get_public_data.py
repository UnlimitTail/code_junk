import os
import sys
import asyncio
import time

appRoot = os.path.dirname(os.path.realpath(__file__))
os.chdir(appRoot)
sys.path.append('../../..')
sys.path.append('../../../bfxapi')


from bfxapi import Client

bfx = Client(
  logLevel='DEBUG',
)

now = int(round(time.time() * 1000))
then = now - (1000 * 60 * 60 * 24 * 10) # 10 days ago

async def log_historical_candles():
  candles = await bfx.rest.get_public_candles('tBTCUSD', 0, then)
  print ("Candles:")
  [ print (c) for c in candles ]

async def log_historical_trades():
  trades = await bfx.rest.get_public_trades('tBTCUSD', 0, then)
  print ("Trades:")
  [ print (t) for t in trades ]

async def log_books():
  orders = await bfx.rest.get_public_books('tBTCUSD')
  # orders = await bfx.rest.get_public_books('xBTCUSD')
  # ...xbtusd
  print ("Order book:")
  [ print (o) for o in orders ]

async def log_ticker():
  ticker = await bfx.rest.get_public_ticker('tBTCUSD')
  print ("Ticker:")
  print (ticker)

async def log_mul_tickers():
  tickers = await bfx.rest.get_public_tickers(['tBTCUSD', 'tETHBTC'])
  print ("Tickers:")
  print (tickers)


from time import sleep

import types
@types.coroutine
def asyncSleep():
    yield from asyncio.sleep(2)

async def waitFunc():
  await asyncSleep()
  
async def run():
  await log_historical_trades()
  #await log_books()
  await waitFunc()
  # await log_historical_candles()
  # await log_ticker()
  # await log_mul_tickers()
  
# t = asyncio.ensure_future(run())

while True:
  t = asyncio.ensure_future(run())
  asyncio.get_event_loop().run_until_complete(t)
  # sleep(1)
  # print('sleep')

asyncio.get_event_loop().close()
