from django.conf.urls.defaults import *
from django.conf import settings

import sb_twitter
import sb_linkedin
import sb_facebook
import sb_sparql

import controller
import merging

urlpatterns = patterns('',
	url(r'^'+settings.APP_URL+'$', controller.index),
	url(r'^'+settings.APP_URL+'filter/$', controller.filter),
	url(r'^'+settings.APP_URL+'myconnections/$', controller.show_connections),
	url(r'^'+settings.APP_URL+'connection/(?P<connection_id>\d+)/$', controller.get_connection_details),
	url(r'^'+settings.APP_URL+'recs/$', controller.get_recommendations),
	url(r'^'+settings.APP_URL+'save_rating/(?P<connection_id>\d+)/$', controller.save_rating),
        # Hari
        url(r'^'+settings.APP_URL+'add_favourites/(?P<connection_id>\d+)/$',controller.add_favourite),
        #following two urls are added for linked in integration
	url(r'^'+settings.APP_URL+'load_linkedin/(?P<dos>\d+)/$', sb_linkedin.load_linkedin),
	url(r'^'+settings.APP_URL+'linkedin_oauth_step1/$', sb_linkedin.linkedin_oauth_step1),
	url(r'^'+settings.APP_URL+'linkedin_oauth_step2/$', sb_linkedin.linkedin_oauth_step2),

	#following two urls are added for facebook oauth integration
	url(r'^'+settings.APP_URL+'load_facebook/$', sb_facebook.load_facebook),
	url(r'^'+settings.APP_URL+'facebook_oauth_step1/$', sb_facebook.facebook_oauth_step1),
	url(r'^'+settings.APP_URL+'facebook_oauth_step2/$', sb_facebook.facebook_oauth_step2),

	#following url lets us set the access token in session
	url(r'^'+settings.APP_URL+'reset_facebook_token/$', sb_facebook.reset_facebook_token),

	#url(r'^'+settings.APP_URL+'load_facebook/$', controller.load_facebook),
	url(r'^'+settings.APP_URL+'load_twitter_friends_and_followers/$', sb_twitter.load_twitter_friends_and_followers),

	#following two urls are added for twitter oauth integration
	url(r'^'+settings.APP_URL+'twitter_oauth_step1/$', sb_twitter.twitter_oauth_step1),
	url(r'^'+settings.APP_URL+'twitter_oauth_step2/$', sb_twitter.twitter_oauth_step2),

	#following urls create a JSON output for the logged in user of his/her connections
	url(r'^'+settings.APP_URL+'create_json/$', controller.createJSON),
	url(r'^'+settings.APP_URL+'create_user_json/$', controller.createUserJSON),

	#following url run the merge function on demand
	url(r'^'+settings.APP_URL+'merge_connections/$', merging.merge_on_demand),
)
