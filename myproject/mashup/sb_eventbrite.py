



EVENTBRITE_CONSUMER_KEY = "LUSYI2XLDPZEA3VSVB"
EVENTBRITE_USER_KEY= "133092139028629534709"
EVENTBRITE_CONSUMER_SECRET = ""
EVENTBRITE_OAUTH_STEP1_URL = SITE_URL+"eventbrite_oauth_step1/"
EVENTBRITE_OAUTH_STEP2_URL = SITE_URL+"eventbrite_oauth_step2/"

def is_eventbrite_authorized(request):
	oauth_acccess_token = request.session.get("session_eventbrite_access_token")	

	if oauth_acccess_token is not None:
		return True
	else:
		return False

def eventbrite_oauth_step1(request):
	#https://www.eventbrite.com/json/event_search?app_key=LUSYI2XLDPZEA3VSVB&keywords=super%20fun&city=Cambridge&within=15&date=This%20Month&user_key=pbotla

	redirectURL = "https://www.facebook.com/dialog/oauth?client_id=" + EVENTBRITE_CONSUMER_KEY + "&redirect_uri=" + EVENTBRITE_CONSUMER_SECRET

	return HttpResponseRedirect(redirectURL)


def eventbrite_oauth_step2(request):	
	oauth_verifier_1 = request.GET['code']

	print "Storing oauth verifier in session", oauth_verifier_1
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

	print "Storing Access Token in session, Access Token: ", facebook_access_token

	request.session["session_facebook_access_token"] = facebook_access_token
	redirectURL = request.session.get("session_facebook_oauth_callingurl")

	print "Redirecting back to URL to fetch facebook data: ", redirectURL
	return HttpResponseRedirect(redirectURL)
