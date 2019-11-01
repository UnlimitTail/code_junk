import os
import sys
sys.path.append('../')

appRoot = os.path.dirname(os.path.realpath(__file__))
os.chdir(appRoot)
sys.path.append('../../..')
sys.path.append('../../../bfxapi')

from bfxapi import Client

bfx = Client(
  #logLevel='DEBUG',
  logLevel='INFO',
  # Verifies that the local orderbook is up to date
  # with the bitfinex servers
  manageOrderBooks=True
)

@bfx.ws.on('error')
def log_error(err):
  print ("Error: {}".format(err))

@bfx.ws.on('order_book_update')
def log_update(data):
  print ("Book update: {}".format(data))

@bfx.ws.on('order_book_snapshot')
def log_snapshot(data):
  print ("Initial book: {}".format(data))

@bfx.ws.on('new_trade')
def log_trade(trade):
  print ("New trade: {}".format(trade))

@bfx.ws.on('subscribed')
def log_subscribed(subscribed):
  print ("subscribed: {}".format(subscribed._ws.messages))


async def start():
  await bfx.ws.subscribe('book', 'tBTCUSD')
  # bfx.ws.subscribe('book', 'tETHUSD')
  # await bfx.ws.subscribe('trades', 'tBTCUSD')

bfx.ws.on('connected', start)
bfx.ws.run()

print('1')
bfx.ws.run()
print('2')

