"""
This module is used to interact with the bitfinex api
"""

from .Client import Client
from .models import (Order, Trade, OrderBook, Subscription, Wallet,
                     Position, FundingLoan, FundingOffer, FundingCredit)
from .websockets.GenericWebsocket import GenericWebsocket

NAME = 'bfxapi'
