from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from models import *

import merging
import json
from pprint import pprint
import StringIO

import urllib2
import threading
import string

# import the logging library
import logging

import sb_sql

# Get an instance of a logger
logger = logging.getLogger("projectx")


SITE_URL = settings.SITE_URL
FACEBOOK_CONSUMER_KEY = settings.FACEBOOK_CONSUMER_KEY
FACEBOOK_CONSUMER_SECRET = settings.FACEBOOK_CONSUMER_SECRET
FACEBOOK_OAUTH_STEP1_URL = SITE_URL +"facebook_oauth_step1/"
FACEBOOK_OAUTH_STEP2_URL = SITE_URL +"facebook_oauth_step2/"
FACEBOOK_CONNECTION_STRING = settings.FACEBOOK_CONNECTION_STRING
FACEBOOK_BATCH_CONNECTION_STRING = settings.FACEBOOK_BATCH_CONNECTION_STRING
#Mising ones - books,movies,music,groups,activities,albums,feed,games,posts,statuses,tagged

FACEBOOK_SCOPE = settings.FACEBOOK_SCOPE

fb_thread_lock = threading.Lock()


def is_facebook_authorized(request):
	oauth_acccess_token = request.session.get("session_facebook_access_token")

	if oauth_acccess_token is not None:
		return True
	else:
		return False

def facebook_oauth_step1(request):
	redirectURL = "https://www.facebook.com/dialog/oauth?client_id=" + FACEBOOK_CONSUMER_KEY  + "&scope=" + FACEBOOK_SCOPE + "&redirect_uri=" + FACEBOOK_OAUTH_STEP2_URL

	return HttpResponseRedirect(redirectURL)

def facebook_oauth_step2(request):
	oauth_verifier_1 = request.GET['code']

#	print "Storing oauth verifier in session", oauth_verifier_1
	request.session["session_facebook_oauth_verifier"] = oauth_verifier_1

	#get the access token from facebook by passing in
	#client_id
	#client_secret
	#redirect URL
	#code from request

	access_token_url = "https://graph.facebook.com/oauth/access_token?client_id=" + FACEBOOK_CONSUMER_KEY + "&redirect_uri=" + FACEBOOK_OAUTH_STEP2_URL + "&client_secret=" + FACEBOOK_CONSUMER_SECRET + "&code=" + oauth_verifier_1

	#call this URL and read the response
	response_access_token = urllib2.urlopen(access_token_url)
	facebook_access_token = response_access_token.read()
	response_access_token.close()

#	print "Storing Access Token in session, Access Token: ", facebook_access_token

	request.session["session_facebook_access_token"] = facebook_access_token
	redirectURL = request.session.get("session_facebook_oauth_callingurl")

#	print "Redirecting back to URL to fetch facebook data: ", redirectURL
	return HttpResponseRedirect(redirectURL)

def reset_facebook_token(request):
	facebook_token = request.GET["facebook_token"]
	request.session["session_facebook_access_token"] = "access_token="+facebook_token
	return HttpResponse("Added Facebook Access token to session. <a href='/"+settings.APP_URL+"load_facebook'>Load Facebook<a>")

def load_facebook(request):

	#check if the authentication tokens are in session, if not call oath handshake
	if is_facebook_authorized(request) is False:
		#store this url in session
#		print "Storing RedirectURL after OAuth: ", request.path
		request.session["session_facebook_oauth_callingurl"] = "http://" + request.get_host()  + request.path

		#redirect to HTTP oath step1
		return HttpResponseRedirect(FACEBOOK_OAUTH_STEP1_URL)

	access_token = request.session.get("session_facebook_access_token")

	me_url = FACEBOOK_CONNECTION_STRING % 'me'
#	print "Calling URL: " + me_url+access_token

	#Parse Projectx user's info from facebook and store it in SBUserProfile
	my_response = None
	try:
		my_response = urllib2.urlopen(me_url+access_token)

	except Exception :
		logger.debug("Error opening Error400URL=" + me_url+access_token)
		print my_response
		print me_url+access_token

	logger.debug("Received my info from facebook")
	my_list = json.load(my_response)
	my_response.close()

	logger.debug("MyID="+ my_list["id"])
	my_id = my_list["id"]
	source = 'facebook'
	#Get SBUserProfile and save facebook id in it
	user_profile = merging.get_or_create_user_profile(request)
	user_profile.source = source
	user_profile.source_id = my_id
	user_profile.save()

	#Create file to write user's facebook profile data
	FACEBOOK_DATAFILE_URL = settings.APP_LOG_DIR + 'fb_user_' + my_id + '.json'
	fp_user_data = open(FACEBOOK_DATAFILE_URL, 'w')
	#Save user's profile data
	#TODO save a flag indicating this is SBUserProfile.
	save_facebook_user(request, my_list, fp_user_data, my_id)

	# Limiting friends to only first settings.FACEBOOK_CONN_COUNT due to timeout errors.
	friends_list_url = "https://graph.facebook.com/me/friends?metadata=1&fields=id,name&limit="+str(settings.FACEBOOK_CONN_COUNT)+"&"
#	print "Calling URL: " + friends_list_url+access_token

	friends_list_response = urllib2.urlopen(friends_list_url+access_token)
#	print "Received friends list from facebook"
	friends_list = json.load(friends_list_response)
	friends_list_response.close()

	user_api_url_template = FACEBOOK_CONNECTION_STRING
	#"https://graph.facebook.com/%s?fields=id,first_name,last_name,birthday,website,email,locale,significant_other,movies,books,languages,education,work,location,hometown,likes,sports,events,interests,groups,music,picture&"


	#Iterate over each user in the list and get details from facebook and then call save_facebook_user method
	#Initial URL '/home/hari/webapps/django/myproject/mashup/data/user_data.json'
	FACEBOOK_DATAFILE_URL = settings.APP_LOG_DIR + 'fb_user_data' + my_id + '.json'
	fp_user_data = open(FACEBOOK_DATAFILE_URL, 'w')

	logger.debug("FBFriendsCount="+ str(len(friends_list["data"])))
	nFriends = len(friends_list["data"])

	#following piece of code uses threads to read data from facebook and save it to database
	NUM_THREADS = settings.FACEBOOK_NUM_OF_THREADS
	BATCH_SIZE = 20
	thread_list = [None]*NUM_THREADS
	all_interactions = []
	nBatches = nFriends/BATCH_SIZE+1

	offset = 0
	for loopCount in range(0, nBatches/NUM_THREADS+1):
		end1 = (loopCount+1)*NUM_THREADS
		if end1 > nBatches:
			end = nBatches - loopCount*NUM_THREADS
		else:
			end = NUM_THREADS

		logger.info('End point'+str(end))

		try:
			for numThreads in range(0,end):
				user_id = friends_list["data"][loopCount*NUM_THREADS + numThreads]
				#user_api_url = user_api_url_template % user_id["id"]
				#new_url = user_api_url+access_token
				new_url = FACEBOOK_BATCH_CONNECTION_STRING+access_token+"&offset="+str(offset)+"&limit="+str(BATCH_SIZE)
				thread_list[numThreads] = threading.Thread(target=read_save_fb_multithread, args=(request, new_url, fp_user_data, my_id))
				thread_list[numThreads].start()
				offset = offset + BATCH_SIZE
			#time.sleep(end/5)
			for numThreads2 in range(0,end):
				thread_list[numThreads2].join()
		except IndexError, e:
			msg = str(datetime.datetime.now()) + " No facebook user_id found, probably due to loading brand page. " + str(IndexError) + str(e)
			print msg
			logger.error(msg)
		except AttributeError, e:
			msg = str(datetime.datetime.now()) + " No thread_list.join, probably due to loading brand page. " + str(AttributeError) + str(e)
			print msg
			logger.error(msg)
	merging.merge(request.user, "facebook") #Commented out as using merge_on_demand

	return HttpResponse("Your Facebook connections have been saved into the database! <a href='/"+settings.APP_URL+"'> Home<a>")

def read_save_fb_multithread(request, new_url, fp_user_data, my_id):
	user_response = urllib2.urlopen(new_url)
	user_data_array = json.load(user_response)
	user_response.close()

	logger.debug("URL=" + new_url)

	for user_data in user_data_array["data"]:
		try:
			fb_thread_lock.acquire()
			save_facebook_user(request, user_data, fp_user_data, my_id)
		except Exception, e:
			print "Exception storing facebook data of user."
			print e
			logger.error("Failed to load FBID=" + str(user_data["id"]))
		finally:
			fb_thread_lock.release()

	#interaction_dict = create_interaction_table(user_data)

	#all_interactions.add(interaction_dict)

	#save to database
	#save_interactions(request, interaction_dict)


def save_interactions(request, interaction_dict):
	#save interactions between user
	posts = interaction_dict["posts"]

	#read connection_ids
	for key in posts.keys():
		#fetch the record from database
		post_count = posts[key]
		ids = string.split(key, "_")
		id1 = ids[0]
		id2 = ids[1]

		links = Link.objects.filter(Id_from=id1, Id_to=id2)
		if len(links) > 0:
			link1 = links[0]
			link1.posts = post_count
			link1.save()

def save_facebook_user(request, user_data, fp_user_data, my_id):
	user_data_stream = StringIO.StringIO()
	pprint(user_data, user_data_stream)
	fp_user_data.write(user_data_stream.getvalue())

	source_id = user_data["id"]
	conn_exists = request.user.connection_profile_set.filter(source_id=source_id)
	if len(conn_exists):
		if len(conn_exists) > 1:
			print "Warning: More than one connection profiles with id %s for user %s" % (source_id, request.user)
		user_profile = conn_exists[0]
		# check if profile was updated in the last settings.PROFILE_REFRESH_INTERVAL days, if yes skip saving new data
		delta_now_lastSaved = merging.get_timedelta(user_profile)
		if delta_now_lastSaved.days >= settings.PROFILE_REFRESH_INTERVAL:
			user_profile.save_facebook_connection_profile(user_data, "facebook", my_id)
			print "Refreshed", user_profile
		user_profile.save()
		logger.debug("Refreshed " + user_data["id"])
		#logger.info("Refreshed" + user_profile)
	else:
		user_profile = Connection_Profile(user=request.user, degree_of_separation=1)
		user_profile.save_facebook_connection_profile(user_data, "facebook", my_id)
		user_profile.save()
		print user_profile

