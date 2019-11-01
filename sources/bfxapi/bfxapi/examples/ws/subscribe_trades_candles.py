import os
import sys
sys.path.append('../')

appRoot = os.path.dirname(os.path.realpath(__file__))
os.chdir(appRoot)
sys.path.append('../../..')
sys.path.append('../../../bfxapi')

from bfxapi import Client

bfx = Client(
  logLevel='DEBUG'
)

@bfx.ws.on('error')
def log_error(err):
  print ("Error: {}".format(err))

@bfx.ws.on('new_candle')
def log_candle(candle):
  print ("New candle: {}".format(candle))

@bfx.ws.on('new_trade')
def log_trade(trade):
  print ("New trade: {}".format(trade))

@bfx.ws.on('subscribed')
def log_subscribed(subscribed):
  print ("subscribed: {}".format(subscribed._ws.messages))


async def start():
  #await bfx.ws.subscribe('candles', 'tBTCUSD', timeframe='1m')
  await bfx.ws.subscribe('trades', 'tBTCUSD')

bfx.ws.on('connected', start)
bfx.ws.run()
