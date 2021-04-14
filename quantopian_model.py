import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from datetime import datetime
from quantopian.pipeline.filters import QTradableStocksUS

# Import the data we uploaded using Self-Serve Data feature of quantopian
# This is the data from the 01/01/2010 - 01/01/2011

from quantopian.pipeline.data.user_5eeab68125ede7003fd733b7 import buyback_2010

def initialize(context):
"""
Called once at the start of the algorithm.
"""
	# Rebalance every day, 1 hour after market open.
	algo.schedule_function(
	rebalance,
	algo.date_rules.every_day(),
	algo.time_rules.market_open(hours=1),
	)
	# Record tracking variables at the end of each day.
	algo.schedule_function(
	record_vars,
	algo.date_rules.every_day(),
	algo.time_rules.market_close(),
	)
	# Create our dynamic stock selector.
	algo.attach_pipeline(make_pipeline(), 'pipeline')
	# Select the maximum position in a particular position = 1%
	context.max_position = 0.01
	# Store the orders that are currently held using their object id
	context.latest_orders = []


def make_pipeline():
"""
A function to create our dynamic stock selector (pipeline). Documentation
on pipeline can be found here:
https://www.quantopian.com/help#pipeline-title
"""
	# Base universe set to the QTradableStocksUS
	base_universe = QTradableStocksUS()
	# Factor of yesterday's close price.
	yesterday_close = USEquityPricing.close.latest
	# The pipe is multi-indexed and has a single boolean column which
	# tells whether there was a buyback or not, on that particular date
	pipe = Pipeline(
	columns={
	'buyback_today': buyback_2010.buyback_announcement_today.latest
	},
	)
	return pipe


def before_trading_start(context, data):
"""
Called every day before market open.
"""
	context.output = algo.pipeline_output('pipeline')
	# In this function I will update which stock/stocks I want to buy
	# These are the securities that we are interested in trading each day.
	req_stocks = []
	# Filter the stock that actually had a buyback announcement that day
	for index, row in context.output.iterrows():
		if row['buyback_today'] == True:
			req_stocks.append(index)
			# Update the security list based on the stocks we want to trade
			context.security_list = req_stocks
			# the function buys the stocks based on the ticker id
			# and updates the list of latest orders by adding the recently bought order


def buy_stocks(context, sid):
	# The functionality of trading with only positive cash remaining
	cash_remaining = context.portfolio.cash
	value = context.portfolio.portfolio_value * context.max_position
	if cash_remaining > value:
		order_id = order_value(sid, value)
		context.latest_orders.append(order_id)


# compute the difference between 2 dates in days
# the dates are passed in string of format YYYY-MM-DD
def days_between(d1, d2):
	d1 = datetime.strptime(d1, "%Y-%m-%d")
	d2 = datetime.strptime(d2, "%Y-%m-%d")
	return abs((d2 - d1).days)


# remove the orders from the current list that have already traded(sold)
def remove_orders(context, orders):
	context.latest_orders = list(set(context.latest_orders) - set(orders))


# Sell any stocks that finish their term of 60 days from
# the list of latest orders
def sell_stocks(context):
	# Store the list of orders to be deleted from the list of latest orders
	orders_to_remove = []
	for order_id in context.latest_orders:
		order_obj = get_order(order_id)
		order_date = str(order_obj.created)
		order_date = order_date.split(' ')[0]
		cur_date = str(get_datetime().date())
	# If the object is held for 60 more days then sell it
	if days_between(order_date, cur_date) >= 60:
		if order_obj.filled > 0:
			order(order_obj.sid, (-1 * order_obj.filled))
			orders_to_remove.append(order_id)
			remove_orders(context, orders_to_remove)


def rebalance(context, data):
"""
Execute orders according to our schedule_function() timing.
"""
	# buy the stock which we want to trade
	for i in context.security_list:
		buy_stocks(context, i)
		# Sell the stocks that have reached the maturity of their holding period
		sell_stocks(context)


def record_vars(context, data):
"""
Plot variables at the end of each day.
"""
	pass


def handle_data(context, data):
"""
Called every minute.
"""
	pass