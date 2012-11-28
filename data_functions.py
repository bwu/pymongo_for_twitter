#!/path/to/python

import dates
import pymongo
from pymongo import Connection
import pytz
from pytz import timezone
import sys

class TwitterDatabase:
	"""
	Class to add Twitter data to database.
	"""
	c = Connection()

	def __init__(self, database_name, handle_name):
		"""
		Initialize the database class using the name of the database and the name of the collection
		"""
		self.db = getattr(self.c, database_name)
		self.handle_name = handle_name

	# Method to wrap all functions in a try and except wrapper.
	def exceptionWrapper(function):
		def wrapper(self, *args, **kwargs):
			try:
				return function(self, *args, **kwargs)
			except KeyboardInterrupt:
				# Print the error and exit
				print "Fail! %s failed for %s due to Keyboard Interrupt!" % (function.__name__, 
					self.handle_name)
				sys.exit()
			except:
				# Print other error:
				print "Fail! %s failed for %s from other exception. Details - " % (function.__name__, 
					self.handle_name)
				print "  ", sys.exc_info()[:2]
		return wrapper

	# Method to get Twitter replies (used in insights.py)
	@exceptionWrapper
	def countReplies(self, collection_name, id_str):
		collection = getattr(self.db, collection_name)
		return collection.find({'handle_name':self.handle_name, 'in_reply_to_status':id_str}).count()

	# Method to query database
	@exceptionWrapper
	def query(self, collection_name, query):
		collection = getattr(self.db, collection_name)
		return collection.find(query)

	# Method to update data in the form of tweets into the mongo database (used for constantly updating tweets).
	@exceptionWrapper
	def insertTweets(self, collection_name, tweets):
		collection = getattr(self.db, collection_name)
		for tweet in tweets:
			identifier = {'status_id':tweet['status_id'], 'handle_name':tweet['handle_name']}
			collection.update(identifier, tweet, upsert=True)

	# Method to set data in the form of tweets into the mongo database (used for frozen tweets).
	@exceptionWrapper
	def updateTweets(self, collection_name, tweets):
		collection = getattr(self.db, collection_name)
		for tweet in tweets:
			identifier = {'status_id':tweet['status_id'], 'handle_name':tweet['handle_name']}
			collection.update(identifier, {'$set':tweet}, upsert=True)

	# Method to insert channel data into the mongo database.
	@exceptionWrapper
	def insertChannelData(self, collection_name, data):
		collection = getattr(self.db, collection_name)
		today = dates.returnToday()
		data['date'] = today
		identifier = {'date':today, 'handle_name':data['handle_name']}
		collection.update(identifier, data, upsert=True)
