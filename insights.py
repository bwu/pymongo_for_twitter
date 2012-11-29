#!/path/to/python

import twitter
import datetime
import bitly_api
from datetime import date, timedelta, datetime, tzinfo
import pymongo
from pymongo import Connection
import pytz
from pytz import timezone
import csv
import codecs
import sys
import os
import json
from dates import *
import data_functions
import itertools

# Connect to bitly API with username braindeer
try:
	bitly_connection = bitly_api.Connection('BITLY_USERNAME', 'BITLY_APIKEY')
except:
	print "Bit.ly Connection Failed"

# Connect to the database and assign the correct name for the database and collection
connection = Connection(tz_aware=True)
db = connection.test    # Change the name of this database if necessary

# Grab bitly clicks for a specific url and screen_name.
def getBitlyClicks(url):
	code = url.rpartition('/')[2]
	try:
		clicks = bitly_connection.clicks(hash = code)[0]['user_clicks']
	except:
		clicks = ''
	return clicks

# Function for chunking arrays.
def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

# Function for figuring out elapsed time since post
def elapsedTime(tweet_date):
	elapsed_time = datetime.strptime(returnNow(),"%Y-%m-%d, %H:%M:%S") - datetime.strptime(tweet_date,"%Y-%m-%d %H:%M:%S")
	if (elapsed_time < timedelta(2)):
		return '2_day'
	elif (elapsed_time < timedelta(7)):
		return '7_day'
	else:
		return 'lifetime'

class TwitterMetrics:
	"""
	Class to retrieve Twitter data for handles.
	"""

	def __init__(self, handle_name, user_id, oauth_token, oauth_token_secret, consumer_key, consumer_secret):
		"""
		Initialize the Twitter class using the four oauth parameters, and set up the twitter objects
		for use in the follow functions.
		"""
		self.handle_name = handle_name
		self.user_id = user_id
		self.t = twitter.Twitter(domain='api.twitter.com', api_version='1.1', 
			auth=twitter.oauth.OAuth(oauth_token, oauth_token_secret, consumer_key, consumer_secret))


	# Function to wrap all functions in a try and except wrapper.
	def exceptionWrapper(function):
		def wrapper(self, *args, **kwargs):
			try:
				return function(self, *args, **kwargs)
			except twitter.api.TwitterHTTPError as e:
				# Print the error and details
				print "Fail! %s failed for %s. Details - " % (function.__name__, 
					self.handle_name)
				print "  Twitter Error Status: %i" % e.e.code
				print "  URL: %s.%s" % (e.uri, e.format)
				print "  Parameters: %s" % e.uriparts
			except KeyboardInterrupt:
				# Print the error and exit
				print "Fail! %s failed for %s due to Keyboard Interrupt!" % (function.__name__, 
					self.handle_name)
				sys.exit()
			except:
				# Print other error:
				print "Fail! %s failed for %s from other exception. Details - " % (function.__name__, 
					self.handle_name)
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print(exc_obj, fname, exc_tb.tb_lineno)
		return wrapper

	# Return the number of remaining API Calls you have for 1 hour.
	@exceptionWrapper
	def remainingAPICalls(self):
		resources = self.t.application.rate_limit_status()['resources']
		remaining_mentions_timeline = resources['statuses']['/statuses/mentions_timeline']['remaining']
		remaining_user_timeline = resources['statuses']['/statuses/user_timeline']['remaining']
		remaining_search = resources['search']['/search/tweets']['remaining']
		remaining_users_show = resources['users']['/users/show/:id']['remaining']
		remaining_users_lookup = resources['users']['/users/lookup']['remaining']
		return {'mentions_timeline':remaining_mentions_timeline, 'user_timeline':remaining_user_timeline, 'search':remaining_search, 'users_show':remaining_users_show, 'users_lookup':remaining_users_lookup}

	# Return the number of remaining API Calls you have for 1 hour.
	@exceptionWrapper
	def remainingAPICalls2(self, resource, sub_resource):
		return self.t.application.rate_limit_status()['resources'][resource][sub_resource]['remaining']

	# Method to get the mentions of a twitter handle
	@exceptionWrapper
	def getMentions(self, minimum_tweets=100):
		results = []
		i=0
		while len(results)<minimum_tweets:
			if i==0:
				response = self.t.statuses.mentions_timeline(include_entities=True, contributor_details=True, include_rts=False, count=50)
			else:
				response = self.t.statuses.mentions_timeline(include_entities=True, contributor_details=True, include_rts=False, count=50, max_id=max_id)
			if not response: break				
			max_id = str(long(response[-1]['id_str'])-1) # Subtracts 1 from the long, and converts back to string
			results.extend(response)
			i += 1
		return results

	# Method to parse the mentions of a twitter handle
	@exceptionWrapper
	def parseMentions(self, tweets):
		results = []
		for tweet in tweets:
			# Parse user data
			user = {}
			user['name'] = tweet['user']['name']
			user['screen_name'] = tweet['user']['screen_name']
			user['location'] = tweet['user']['location']
			user['followers_count'] = tweet['user']['followers_count']
			user['friends_count'] = tweet['user']['friends_count']
			user['statuses_count'] = tweet['user']['statuses_count']

			# Parse tweet data
			status_id = tweet['id_str']
			in_reply_to_status = tweet['in_reply_to_status_id_str']
			tweet_link = "http://twitter.com/#!/%s/status/%s" % (user['screen_name'], status_id)
			created_at = convertToESTFromNaive(datetime.strptime(tweet['created_at'],"%a %b %d %H:%M:%S +0000 %Y")).strftime("%Y-%m-%d %H:%M:%S")
			url = ""
			if tweet['entities']['urls']:
				try:
					url = tweet['entities']['urls'][0]['display_url']
				except KeyError:
					url = tweet['entities']['urls'][0]['url']
			retweet_count = tweet['retweet_count']
			text = tweet['text']
			entries = {'status_id' : status_id, 'handle_name' : self.handle_name, 
				'tweet_link' : tweet_link, 'date' : created_at, 'text' : text, 
				'in_reply_to_status' : in_reply_to_status, 'user' : user, 'url' : url,
				'retweet_count' : retweet_count }
			results.append(entries)
		return results

	# Method to get the posts from a twitter handle
	@exceptionWrapper
	def getPosts(self, minimum_tweets=100):
		results = []
		i=0
		while len(results)<minimum_tweets:
			if i==0:
				response = self.t.statuses.user_timeline(trim_user=True, include_rts=False, count=200)
			else:
				response = self.t.statuses.user_timeline(trim_user=True, include_rts=False, count=200, max_id=max_id)
			if not response: break		
			max_id = str(long(response[-1]['id_str'])-1) # Subtracts 1 from the long, and converts back to string
			results.extend(response)
			i += 1
		return results

	# Method to get the posts from a twitter handle
	@exceptionWrapper
	def parsePosts(self, tweets):
		d = data_functions.TwitterDatabase(handle_name=self.handle_name, database_name='metrics_2')
		posts = []
		replies = []
		for tweet in tweets:
			status_id = tweet['id_str']
			tweet_link = "http://twitter.com/#!/%s/status/%s" % (self.user_id, status_id)
			created_at = convertToESTFromNaive(datetime.strptime(tweet['created_at'],"%a %b %d %H:%M:%S +0000 %Y")).strftime("%Y-%m-%d %H:%M:%S")
			url = ""
			bitly_clicks = ""
			if tweet['entities']['urls']:
				try:
					url = tweet['entities']['urls'][0]['display_url']
				except KeyError:
					url = tweet['entities']['urls'][0]['url']
				finally:
					bitly_clicks = getBitlyClicks(url)
			reply_count = d.countReplies("twitter_mentions", status_id)
			retweet_count = tweet['retweet_count']
			text = tweet['text']
			entries = {'status_id' : status_id, 'tweet_link' : tweet_link, 'date' : created_at, 
				'text' : text, 'url' : url, 'retweet_count' : retweet_count, 'handle_name' : self.handle_name, 
				'bitly_clicks' : bitly_clicks, 'reply_count' : reply_count}
			if text.startswith("@"): replies.append(entries)
			else: posts.append(entries)
		return {'posts':posts, 'replies':replies}

	# Method to get the posts from a twitter handle
	@exceptionWrapper
	def parseFrozenPosts(self, tweets):
		d = data_functions.TwitterDatabase(handle_name=self.handle_name, database_name='metrics_2')
		posts = []
		replies = []
		for tweet in tweets:
			status_id = tweet['id_str']
			tweet_link = "http://twitter.com/#!/%s/status/%s" % (self.user_id, status_id)
			created_at = convertToESTFromNaive(datetime.strptime(tweet['created_at'],"%a %b %d %H:%M:%S +0000 %Y")).strftime("%Y-%m-%d %H:%M:%S")
			url = ""
			bitly_clicks = ""
			if tweet['entities']['urls']:
				try:
					url = tweet['entities']['urls'][0]['display_url']
				except KeyError:
					url = tweet['entities']['urls'][0]['url']
				finally:
					bitly_clicks = getBitlyClicks(url)
			reply_count = d.countReplies("twitter_mentions", status_id)
			retweet_count = tweet['retweet_count']
			elapsed_time = elapsedTime(created_at)
			text = tweet['text']
			entries = {'status_id' : status_id, 'tweet_link' : tweet_link, 'date' : created_at, 
				'text' : text, 'url' : url,'handle_name' : self.handle_name, elapsed_time : {'retweet_count' : retweet_count,  
				'bitly_clicks' : bitly_clicks, 'reply_count' : reply_count}}
			if text.startswith("@"): replies.append(entries)
			else: posts.append(entries)
		return {'posts':posts, 'replies':replies}

	# Method to get tweets containing a hashtag
	@exceptionWrapper
	def getHashtags(self, hashtag, minimum_tweets=100):
		results = []
		i=0
		while len(results)<minimum_tweets:
			if i==0:
				response = self.t.search.tweets(q=hashtag, result_type='recent', count=100)
			else:
				response = self.t.search.tweets(q=hashtag, result_type='recent', count=100, max_id=max_id)
			if not response['statuses']: break
			max_id = str(long(response['statuses'][-1]['id_str'])-1) # Subtracts 1 from the long, and converts back to string
			results.extend(response['statuses'])
			i += 1
		return {'query':response['search_metadata']['query'], 'results':results}

	# Method to parse tweets containing a hashtag
	@exceptionWrapper
	def parseHashtags(self, tweets):
		results = []
		query = tweets['query']
		for tweet in tweets['results']:
			# Parse user data
			user = {}
			user['name'] = tweet['user']['name']
			user['screen_name'] = tweet['user']['screen_name']
			user['location'] = tweet['user']['location']
			user['followers_count'] = tweet['user']['followers_count']
			user['friends_count'] = tweet['user']['friends_count']
			user['statuses_count'] = tweet['user']['statuses_count']

			# Parse Tweet data
			status_id = tweet['id_str']
			in_reply_to_screen_name = tweet['in_reply_to_screen_name']
			tweet_link = "http://twitter.com/#!/%s/status/%s" % (user['screen_name'], status_id)
			created_at = convertToESTFromNaive(datetime.strptime(tweet['created_at'],"%a %b %d %H:%M:%S +0000 %Y")).strftime("%Y-%m-%d %H:%M:%S")
			url = ""
			if tweet['entities']['urls']:
				try:
					url = tweet['entities']['urls'][0]['display_url']
				except KeyError:
					url = tweet['entities']['urls'][0]['url']
			retweet_count = tweet['retweet_count']
			text = tweet['text']
			entries = {'status_id' : status_id, 'tweet_link' : tweet_link, 'date': created_at, 
				'text' : text, 'user' : user, 'handle_name' : self.handle_name, 'query' : query, 
				'in_reply_to_screen_name' : in_reply_to_screen_name, 'url' : url, 
				'retweet_count' : retweet_count }
			results.append(entries)
		return results

	# Get public Twitter handle data
	@exceptionWrapper
	def getChannelData(self):
		response = self.t.users.show(user_id=self.user_id)
		return response

	# Parse public Twitter handle data
	@exceptionWrapper
	def parseChannelData(self, data):
		name = data['name']
		followers_count = data['followers_count']
		total_tweets = data['statuses_count']
		total_lists	= data['listed_count']
		friends_count = data['friends_count']
		entries = { 'followers_count' : followers_count, 'total_tweets' : total_tweets, 
			'total_lists' : total_lists, 'friends_count' : friends_count, 
			'handle_name' : self.handle_name }
		return entries

