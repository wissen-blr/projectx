import time

from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from models import *

import merging

import json
import threading
import oauth2 as oauth
from linkedin import linkedin

import logging

# Get an instance of a logger
logger = logging.getLogger("sbutler")


SITE_URL = settings.SITE_URL

LINKEDIN_CONSUMER_KEY = settings.LINKEDIN_CONSUMER_KEY
LINKEDIN_CONSUMER_SECRET = settings.LINKEDIN_CONSUMER_SECRET
LINKEDIN_OAUTH_STEP1_URL = SITE_URL+"linkedin_oauth_step1/"
LINKEDIN_OAUTH_STEP2_URL = SITE_URL+"linkedin_oauth_step2/"
LINKEDIN_SEARCH_STRING =    "http://api.linkedin.com/v1/people-search:(people:(id,headline,first-name,last-name,location:(name),num-connections,specialties,interests,positions,skills,educations,twitter-accounts,phone-numbers,main-address,picture-url,public-profile-url,date-of-birth,last-modified-timestamp,relation-to-viewer,num-recommenders,recommendations-received,following,job-bookmarks,group-memberships,related-profile-views,languages),num-results)?start=1&count="+str(settings.LINKEDIN_SEARCH_COUNT)+"&network=S&format=json"
LINKEDIN_CONNECTION_STRING = "http://api.linkedin.com/v1/people/~/connections:(id,headline,first-name,last-name,location:(name),num-connections,specialties,interests,positions,skills,educations,twitter-accounts,phone-numbers,main-address,picture-url,public-profile-url,date-of-birth,last-modified-timestamp,relation-to-viewer,num-recommenders,recommendations-received,following,job-bookmarks,group-memberships,related-profile-views,languages)?format=json&count=" + str(settings.LINKEDIN_CONN_COUNT)

li_thread_lock = threading.Lock()

def load_linkedin(request, dos):
	# print "DOS", dos

	if request.user.is_authenticated():
		print "User is logged into SB"
	else:
		return HttpResponse("You are not logged in! <a href='/accounts/login/'>Login</a>")

	#check if the authentication tokens are in session, if not call oath handshake
	if is_linkedin_authorized(request) is False:
		#store this url in session
		# print "Storing RedirectURL after OAuth: ", request.path
		request.session["session_linkedin_oauth_callingurl"] = "http://" + request.get_host()  + request.path

		#redirect to HTTP oath step1
		return HttpResponseRedirect(LINKEDIN_OAUTH_STEP1_URL)

	access_token = 	request.session.get("session_linkedin_access_token")
	access_token_secret = 	request.session.get("session_linkedin_access_token_secret")
	# print "Access Token", access_token, "DOS ", dos
	# print "Access Token Secret", access_token_secret, "DOS ", dos

	content = get_linkedin_data_old(request, dos, access_token, access_token_secret)

	# Storing LinkedIn data into file to look at data
	if dos==u'1':
		LINKEDIN_DATAFILE_URL = settings.APP_LOG_DIR + 'li_user_data_'+request.user.username+'.json'
		li_user_data = open(LINKEDIN_DATAFILE_URL, 'w')
	else:
		LINKEDIN_DATAFILE_URL = settings.APP_LOG_DIR + 'li_user_search_'+request.user.username+'.json'
		li_user_data = open(LINKEDIN_DATAFILE_URL, 'a')
		li_user_data.write('\n')
	li_user_data.writelines(content)

	# Parsing LinkedIn JSON data and storing it into database
	friends_list = json.loads(content)
	if dos==u'1':
		save_linkedin_conn_multithread(request, friends_list)
	else:
		errorCode_exists = nvl(friends_list, 'errorCode')
		if errorCode_exists is not None:
			msg = "Error in retrieving LinkedIn search results"
			logger.error(msg)
			print msg
			msg = "errorCode:"+str(friends_list['errorCode'])+" message:"+str(friends_list['message'])
			logger.error(msg)
			print msg
		elif friends_list['people']['values']:
			for friend in friends_list['people']['values']:
				try:
					source_id = nvl(friend, "id")
					conn_exists = request.user.connection_profile_set.filter(source_id=source_id)
					if not len(conn_exists):
						# save connection
						c_profile = Connection_Profile(user=request.user, degree_of_separation=2)
						c_profile.save_linkedin_connection_profile(friend)
						c_profile.save()
				except Exception, e:
					print "Exception:", e, nvl(friend, "id")
					logger.error("Exception " + str(sys.exc_info()))

	if dos == "1":
#		merging.merge(request.user, "linkedin")
		return HttpResponse("Your connections have been saved into the database! <a href='/"+settings.APP_URL+"'>Home<a>")
	else:
		return

def save_linkedin_conn_multithread(request, friends_list):
	try:
#		li_thread_lock.acquire()
		#If friends_list["values"] doesn't exist, you are probably not getting linkedin data
		if nvl(friends_list, "values") is None:
			return
		else:
			logger.debug("NumberOfLIFriends="+ str(len(friends_list["values"])))
			nFriends = len(friends_list["values"])

			NUM_THREADS = 50
			thread_list = [None]*NUM_THREADS

			for loopCount in range(0, nFriends/NUM_THREADS+1):
				end1 = (loopCount+1)*NUM_THREADS
				if end1 > nFriends:
					end = nFriends - loopCount*NUM_THREADS
				else:
					end = NUM_THREADS

	#			logger.debug("EndPoint="+ str(end))

				for numThreads in range(0,end):
					friend = friends_list['values'][loopCount*NUM_THREADS + numThreads]
					thread_list[numThreads] = threading.Thread(target=save_single_linkedin_conn, args=(request, friend))
					thread_list[numThreads].start()
#				print "starting time.sleep function"
#				time.sleep(end/5)
				for numThreads2 in range(0,end):
					thread_list[numThreads2].join()
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in save_linkedin_conn_multithread") + str(e)
		print msg
		logger.error(msg)
#	finally:
#		li_thread_lock.release()

def save_single_linkedin_conn(request, friend):
	try:
		source_id = nvl(friend, "id")
		conn_exists = request.user.connection_profile_set.filter(source_id=source_id)

		li_thread_lock.acquire()
		# If connection profile doesn't exist for current user, create new. Else, update existing.
		if not len(conn_exists):
			# save connection
			c_profile = Connection_Profile(user=request.user, degree_of_separation=1)
			c_profile.save_linkedin_connection_profile(friend)
			c_profile.save()
		else:
			if len(conn_exists) > 1:
				print "Warning: More than one connection profiles with id %s for user %s" % (source_id, request.user)
			c_profile = conn_exists[0]
			c_profile.degree_of_separation = 1
			# print c_profile, "degree_of_separation changed to 1"
			# check if profile was updated in the last PROFILE_REFRESH_INTERVAL days, if yes skip saving new data
			delta_now_lastSaved = merging.get_timedelta(c_profile)
			if delta_now_lastSaved.days >= settings.PROFILE_REFRESH_INTERVAL:
				c_profile.save_linkedin_connection_profile(friend)
			c_profile.save()
	except Exception, e:
		print "Exception:", e, nvl(friend, "id")
	finally:
		li_thread_lock.release()

def get_linkedin_data_old(request, dos, atoken, atoken_secret):

	if dos == "1":
		# URL to get LinkedIn 1st degree connections through connections API
		#url = "http://api.linkedin.com/v1/people/~/connections:(id,headline,first-name,last-name,location:(name),num-connections,specialties,interests,positions,skills,educations,twitter-accounts,phone-numbers,main-address,picture-url,public-profile-url)?format=json&count=" + str(settings.LINKEDIN_CONN_COUNT)
		url = LINKEDIN_CONNECTION_STRING
		# print "LinkedIn Connections URL: ", url
	else:
		#working URL for search API to get limited number of LinkedIn search API results
		location = request.session.get("session_location")
		company = request.session.get("session_company")
		industry = request.session.get("session_industry")
		# print "Parameters for LinkedIn Search: ", location, company, industry

		#url = "http://api.linkedin.com/v1/people-search:(people:(id,headline,first-name,last-name,location:(name),num-connections,specialties,interests,positions,skills,educations,twitter-accounts,phone-numbers,main-address,picture-url,public-profile-url),num-results)?start=1&count="+str(settings.LINKEDIN_SEARCH_COUNT)+"&network=S&format=json&keywords=" + location + "%20" + company + "%20" + industry
		url = LINKEDIN_SEARCH_STRING + "&keywords=" + location + "%20" + company + "%20" + industry
		logger.debug("LinkedInSearchURL=" + url)

	consumer = oauth.Consumer(LINKEDIN_CONSUMER_KEY,LINKEDIN_CONSUMER_SECRET)

	# print atoken
	# print atoken_secret

	token1 = oauth.Token(key=atoken, secret=atoken_secret)

	client2 = oauth.Client(consumer, token1)
	resp1, content1 = client2.request(url)
	# print resp1
	#print content1

	#f = open('result.xml', 'w')
	#f.write(content1)
	return content1

def is_linkedin_authorized(request):
	oauth_acccess_token = request.session.get("session_linkedin_access_token")
	oauth_acccess_token_secret = request.session.get("session_linkedin_access_token_secret")

	if (oauth_acccess_token is not None) and (oauth_acccess_token_secret is not None):
		return True
	else:
		return False

def linkedin_oauth_step1(request):
	api = linkedin.LinkedIn(LINKEDIN_CONSUMER_KEY, LINKEDIN_CONSUMER_SECRET, LINKEDIN_OAUTH_STEP2_URL)
	result = api.request_token()
#	print "LinkedIn Roquest Token: ", api._request_token
#	print "LinkedIn Roquest Token Secret: ", api._request_token_secret

	request.session["session_linkedin_request_token_secret"] = api._request_token_secret
	redirectURL = api.get_authorize_url(request_token = api._request_token)
#	print "RedirectURL: ", redirectURL

	return HttpResponseRedirect(redirectURL)


def linkedin_oauth_step2(request):
	oauth_token_1 = request.GET['oauth_token']
	oauth_verifier_1 = request.GET['oauth_verifier']

#	print "Storing oauth verifier in session",  " Request Token: ", oauth_token_1, "Oauth Verifier: ", oauth_verifier_1
	request.session["session_linkedin_oauth_token"] = oauth_token_1
	request.session["session_linkedin_oauth_verifier"] = oauth_verifier_1

	rts_session = request.session.get("session_linkedin_request_token_secret")
#	print "Request token secret from session: ", rts_session

	DUMMY_CALLBACK_URL = SITE_URL

	# Call back url in this step2 is just a dummy and is not used
	api = linkedin.LinkedIn(LINKEDIN_CONSUMER_KEY, LINKEDIN_CONSUMER_SECRET, DUMMY_CALLBACK_URL)

	result = api.access_token(request_token = oauth_token_1,  request_token_secret = rts_session, verifier = oauth_verifier_1)

#	print "Storing Access Token in session",  " Access Token: ", api._access_token, "Access Token Secret : ", api._access_token_secret
	request.session["session_linkedin_access_token"] = api._access_token
	request.session["session_linkedin_access_token_secret"] = api._access_token_secret

	redirectURL = request.session.get("session_linkedin_oauth_callingurl")

#	print "Redirecting back to URL to fetch linkedin data: ", redirectURL
	return HttpResponseRedirect(redirectURL)


