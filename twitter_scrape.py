#!/path/to/python

import insights
import data_functions
import pymongo
import dates

# Name consumer key and consumer key secret
consumer_key = 'CONSUMER_KEY'
consumer_secret = 'CONSUMER_SECRET'

# Name database and connect to database
database_name = 'DATABASE_NAME'
metrics_database = getattr(pymongo.Connection(), database_name)


print "------------------------------------------------------------"
print "Scrape started at %s" % dates.returnNow()


# Get Twitter data for each handle
for handle in metrics_database.handles.find({'twitter':{'$exists':True},
	'twitter_oauth_token':{'$exists':True}, 'twitter_oauth_token_secret':{'$exists':True},
	'name':{'$exists':True}}):
	
	# Get the handle name, user id, and oauth token
	handle_name = handle['name']
	user_id = handle['twitter']
	oauth_token = handle['twitter_oauth_token']
	oauth_token_secret = handle['twitter_oauth_token_secret']
	twitter_hashtags = handle['twitter_hashtags']

	# Connect to Twitter and the database
	t = insights.TwitterMetrics(handle_name, user_id, oauth_token, oauth_token_secret, consumer_key, consumer_secret)
	d = data_functions.TwitterDatabase(handle_name=handle_name, database_name=database_name)

	# Get mentions, parse and insert into database
	mentions = t.getMentions(500)
	if mentions:
		parsed_mentions = t.parseMentions(mentions)
		d.insertTweets("twitter_mentions",parsed_mentions)
		mentions = []

	# Get posts, parse, and insert into database
	posts = t.getPosts(500)
	if posts:
		parsed_posts = t.parseFrozenPosts(posts)
		d.updateTweets("twitter_content",parsed_posts['posts'])
		d.updateTweets("twitter_replies",parsed_posts['replies'])
		posts = []
	
	# Get hashtags, parse and insert into database
	for hashtag in twitter_hashtags:
		tweets_with_hashtags = t.getHashtags(hashtag, 500)
		if tweets_with_hashtags:
			parsed_tweets_with_hashtags = t.parseHashtags(tweets_with_hashtags)
			d.insertTweets("twitter_hashtags",parsed_tweets_with_hashtags)
			tweets_with_hashtags = []

	#Get channel data, parse and insert into database
	channel_data = t.getChannelData()
	if channel_data:
		parsed_channel = t.parseChannelData(channel_data)
		d.insertChannelData("twitter_channel",parsed_channel)
		channel_data = []

	print "%s remaining API calls: %s" % (handle_name, t.remainingAPICalls())


print "Scrape ended at %s" % dates.returnNow()
print "------------------------------------------------------------\n"