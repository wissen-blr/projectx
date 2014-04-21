from django.http import HttpResponse, HttpResponseRedirect
from models import *

import merging

import json
from pprint import pprint
import StringIO
import urlparse

#from rdflib import Graph, RDF
#from rdflib import URIRef, Literal, BNode

import oauth2 as oauth
from django.conf import settings

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("projectx")

SITE_URL = settings.SITE_URL

TWITTER_CONSUMER_KEY = settings.TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET = settings.TWITTER_CONSUMER_SECRET
TWITTER_OAUTH_STEP1_URL = settings.SITE_URL +"twitter_oauth_step1/"
TWITTER_OAUTH_STEP2_URL = settings.SITE_URL +"twitter_oauth_step2/"
TWITTER_CONN_COUNT = settings.TWITTER_CONN_COUNT
TWITTER_BATCH_COUNT = settings.TWITTER_BATCH_COUNT
TWITTER_CALLBACK_URL = settings.TWITTER_CALLBACK_URL

def is_twitter_authorized(request):
	oauth_acccess_token = request.session.get("session_twitter_access_token")

	if oauth_acccess_token is not None:
		return True
	else:
		return False


def twitter_oauth_step1(request):

	request_token_url = "http://twitter.com/oauth/request_token?oauth_callback=" + TWITTER_CALLBACK_URL
	access_token_url = 'http://twitter.com/oauth/access_token'
	authorize_url = 'http://twitter.com/oauth/authorize'
	consumer = oauth.Consumer(TWITTER_CONSUMER_KEY,TWITTER_CONSUMER_SECRET)
	client = oauth.Client(consumer)
	resp, content = client.request(request_token_url, "GET")
	#query_param_list = string.rsplit(content, "&", 100)

	request_token = dict(urlparse.parse_qs(content))
	roauth_token = request_token['oauth_token'][0]
	roauth_token_secret = request_token['oauth_token_secret'][0]

	request.session["session_twitter_oauth_token"] = roauth_token
	request.session["session_twitter_oauth_token_secret"] = roauth_token_secret

	print "Step1: oauth_token = " + roauth_token
	print "Step1: oauth_token_secret = " + roauth_token_secret

	new_authorize_url = authorize_url+'?oauth_token='+roauth_token
	# +"&oauth_token_secret="+roauth_token_secret + "&ABCD=TTTT"

	return HttpResponseRedirect(new_authorize_url)

	#redirectURL = "https://api.twitter.com/oauth/request_token?oauth_consumer_key=" + TWITTER_CONSUMER_KEY + "&oauth_consumer_secret=" + TWITTER_CONSUMER_SECRET + "&oauth_callback value=http://localhost:8000/twitter_oauth_step2/"
	#+ "&redirect_uri=" + TWITTER_OAUTH_STEP2_URL
#	return HttpResponseRedirect(redirectURL)

def twitter_oauth_step2(request):
	try:
		oauth_verifier = request.GET['oauth_verifier']
		oauth_token = request.GET['oauth_token']

	#	print "Storing oauth verifier in session", oauth_verifier_1
		request.session["session_twitter_oauth_verifier"] = oauth_verifier

		oauth_token_secret = request.session.get("session_twitter_oauth_token_secret")

		#get the access token from twitter by passing in
		#client_id
		#client_secret
		#redirect URL
		#code from request

		print "Step2 : OAuth Verifier = " + oauth_verifier
		print "Step2 : Oauth Token = " + oauth_token
		if (oauth_token_secret != None):
			print "Step2: Oauth Token Secret = " + oauth_token_secret

		#access_token_url = "https://api.twitter.com/oauth/access_token?oauth_consumer_key=7kwAPWaK4CAoehnuX9401w&oauth_consumer_secret=y7uyaP1Zmn6dowA0Q303aBXhnwqyLtrGjwL4m5kbNs&oauth_verifier=" + oauth_verifier_1 + "&oauth_token=" + oauth_token + "&oauth_token_secret=" + oauth_token_secret
		access_token_url = "https://api.twitter.com/oauth/access_token"

		token = oauth.Token(oauth_token, oauth_token_secret)
		token.set_verifier(oauth_verifier)

		consumer = oauth.Consumer(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
		client = oauth.Client(consumer, token)

		resp, content = client.request(access_token_url, "POST")
		access_token = dict(urlparse.parse_qsl(content))

		twitter_access_token = access_token['oauth_token']
		twitter_access_token_secret = access_token['oauth_token_secret']
		userid = access_token['user_id']
		screenname = access_token['screen_name']

	#	print "Storing Access Token in session, Access Token: ", twitter_access_token

		request.session["session_twitter_access_token"] = twitter_access_token
		request.session["session_twitter_access_token_secret"] = twitter_access_token_secret

		redirectURL = request.session.get("session_twitter_oauth_callingurl")

	#	print "Redirecting back to URL to fetch twitter data: ", redirectURL
		return HttpResponseRedirect(redirectURL)
	except Exception, e:
		msg = str(datetime.datetime.now()) + " " + str(Exception) + str(e)
		print msg
		logger.error(msg)
		return HttpResponse("Twitter connections couldn't be loaded. Please try again later. <a href='/'>Home</a>")


def load_twitter(request, my_id, type):
	user_data_stream = StringIO.StringIO()

	access_token = request.session.get("session_twitter_access_token")
	access_secret = request.session.get("session_twitter_access_token_secret")

	# Create your consumer with the proper key/secret.
	consumer = oauth.Consumer(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
	#url1="http://api.twitter.com/1/followers/ids.json?screen_name=akashbhatia"

	url1="http://api.twitter.com/1/" + type + "/ids.json?"
	url2 = "http://api.twitter.com/1/users/lookup.json?"
	token1 = oauth.Token(key=access_token, secret=access_secret)

	client2 = oauth.Client(consumer, token1)
	resp1, content1 = client2.request(url1)
	#print resp1
	print content1

	friends_list = json.loads(content1)

	twitter_followers = settings.APP_LOG_DIR + 'twitter_' + type + '.json'
	fp_twitter = open(twitter_followers, 'w')

	filtered_friends_list = filter_recently_saved(request.user, friends_list["ids"])

	#Batch requests users here
	length = len(filtered_friends_list)
	if length > TWITTER_CONN_COUNT:
		length = TWITTER_CONN_COUNT

	if length > 0:
		num_loops = length / TWITTER_BATCH_COUNT
		if length % TWITTER_BATCH_COUNT > 0:
			num_loops = num_loops + 1
	else:
		num_loops = 0

	for loop in range(0, num_loops):
		if loop == num_loops - 1:
			end_count = length - TWITTER_BATCH_COUNT*(loop)
		else:
			end_count = TWITTER_BATCH_COUNT

		id_list = ""
		for i in range(0, end_count):
			index = loop*TWITTER_BATCH_COUNT + i
			id_list = id_list + str(filtered_friends_list[index]) + ","

		user_api_url = url2+"user_id="+id_list

	#for user_id in friends_list["ids"]:
	#	user_id = friends_list["ids"][10]
	#	user_api_url = url2+"user_id="+str(user_id)

		print user_api_url
		client3 = oauth.Client(consumer, token1)
		resp2,content2 = client3.request(user_api_url)
		if content2 != None:
			#user_response = urllib2.urlopen(user_api_url+access_token)
			twitter_user_data = json.loads(content2)
			#load_twitter_followers(request)
			#iteratre thru each user and load it

			for i in range(0, end_count):
				save_twitter_user(request, twitter_user_data[i], fp_twitter, type, my_id)

		loop = loop + 1

	merging.merge(request.user, "twitter") #Commented out as using merge_on_demand

	return


def load_user_profile(request):
	user_data_stream = StringIO.StringIO()

	#check if the authentication tokens are in session, if not call oath handshake
	if is_twitter_authorized(request) is False:
		#store this url in session
#		print "Storing RedirectURL after OAuth: ", request.path
		request.session["session_twitter_oauth_callingurl"] = "http://" + request.get_host()  + request.path

		#redirect to HTTP oath step1
		return HttpResponseRedirect(TWITTER_OAUTH_STEP1_URL)

	access_token = request.session.get("session_twitter_access_token")
	access_secret = request.session.get("session_twitter_access_token_secret")

	# Create your consumer with the proper key/secret.
	consumer = oauth.Consumer(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
	#url1="http://api.twitter.com/1/followers/ids.json?screen_name=akashbhatia"

	url1="http://api.twitter.com/1/account/verify_credentials.json"

	token1 = oauth.Token(key=access_token, secret=access_secret)

	client2 = oauth.Client(consumer, token1)
	resp1, content1 = client2.request(url1)
	#print resp1
	print content1

	user_profile = json.loads(content1)
	twitter_id = user_profile["id"]

	url_feed = "http://api.twitter.com/1/statuses/user_timeline.json"
	resp2, content2 = client2.request(url_feed)
	print content2
	
	user_feed = json.loads(content2)
	save_twitter_feed(request, twitter_id, user_feed)

	print get_user_twitter_feed(request)
	
	return twitter_id

def save_twitter_feed(request, my_id, user_feed):
	for i in range(len(user_feed)):
		json_data = user_feed[i]
		twitter_feed = Twitter_Feed()
		twitter_feed.save_twitter_feed(json_data, request.user.id, my_id)
		twitter_feed.save()
	return
	
def filter_recently_saved(user, list):
	#check if the source_ids exist in database
	new_list = []
	for i in range(len(list)):
		conn_exists = user.connection_profile_set.filter(source_id=list[i])
		if len(conn_exists):
			if len(conn_exists) > 1:
				print "Warning: More than one connection profiles with id %s for user %s" % (list[i], user)
			user_profile = conn_exists[0]
			# check if profile was updated in the last settings.PROFILE_REFRESH_INTERVAL days, if yes skip saving new data
			delta_now_lastSaved = merging.get_timedelta(user_profile)
			if delta_now_lastSaved.days >= settings.PROFILE_REFRESH_INTERVAL:
				#this id was saved more than refresh interval days back, so needs to be refreshed
				new_list.append(list[i])

		else:
			new_list.append(list[i])

	return new_list


def load_twitter_friends_and_followers(request):
	#check if the authentication tokens are in session, if not call oath handshake
	if is_twitter_authorized(request) is False:
		#store this url in session
#		print "Storing RedirectURL after OAuth: ", request.path
		request.session["session_twitter_oauth_callingurl"] = "http://" + request.get_host()  + request.path

		#redirect to HTTP oath step1
		return HttpResponseRedirect(TWITTER_OAUTH_STEP1_URL)

	my_id = load_user_profile(request)
	load_twitter(request, my_id, "friends")
	load_twitter(request, my_id, "followers")
	return HttpResponse("Your Twitter Followers and Friends have been saved into the database! <a href='/"+settings.APP_URL+"'> Home<a>")


def save_twitter_user(request, user_data, fp_user_data, type, my_id):
	user_data_stream = StringIO.StringIO()
	print "Saving Twitter " + type + " to database"
	pprint(user_data, user_data_stream)
	fp_user_data.write(user_data_stream.getvalue())

	user_profile = Connection_Profile(user=request.user, degree_of_separation=1, birthday = "2000-01-01")
	user_profile.save_twitter_profile(user_data, "twitter", type, my_id)
	user_profile.save()


def get_user_twitter_feed(request):
	user_feeds = Twitter_Feed.objects.filter(user_id=request.user.id)
	
	feed_list = []
	for feed in user_feeds:
		feed_list.append(feed.text)
		
	return feed_list	
		

	
