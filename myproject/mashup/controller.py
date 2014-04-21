from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils.encoding import smart_str, smart_unicode

#for creating a JSON output
from django.core import serializers
from django.utils import simplejson

from models import *

import json
import re

from pprint import pprint
import StringIO

import urllib2
import urlparse
import threading
import time
from django.db import connection, transaction
import string
import datetime

import sb_twitter
import sb_linkedin
import sb_facebook
import sb_sparql
import sb_sql
import merging

import urllib
import sys
#from rdflib import Graph, RDF
#from rdflib import URIRef, Literal, BNode
from rdflib import Namespace
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")

from SPARQLWrapper import SPARQLWrapper, JSON

import oauth2 as oauth
from linkedin import linkedin

from django.conf import settings

import sys

from operator import itemgetter, attrgetter
# import the logging library
import logging
from sb_sparql import *

# Get an instance of a logger
logger = logging.getLogger("projectx")

#functions for analytics shown on index.html using function index
def get_locations(user_id):
	print user_id
	raw_locations_list = execute_query("select mashup_location.name, count( mashup_location.name) from mashup_connection_profile, mashup_location where mashup_location.id = mashup_connection_profile.current_location_id and  mashup_connection_profile.user_id = %s group by mashup_location.name order by count( mashup_location.name) desc" % (user_id))
	location_list = []
	for location_tuple in raw_locations_list:
		location = location_tuple[0]
		location = sb_sql.strip_location(location)
		new_location_tuple = (location, location_tuple[1])
		location_list.append(new_location_tuple)
	return location_list

def get_all_jobs(connection, merged_profile):
	all_jobs_list = []
	jobs_list = get_work_info(connection, merged_profile)[1]
	#Get current industry for Google search
	for job in jobs_list:
		all_jobs_list.append(job.position)
	return all_jobs_list

def get_industries(user_id):
	print user_id
	industry_list = execute_query("select mashup_work_info.industry, count(mashup_work_info.industry) from mashup_connection_profile, mashup_work_info where mashup_work_info.connection_profile_id  = mashup_connection_profile.id and  mashup_connection_profile.user_id = %s group by mashup_work_info.industry order by count( mashup_work_info.industry) desc" % (user_id))
	industry_list = list(industry_list)
	if len(industry_list)>0:
		blank_industries_list = []
		for (counter, ind_tuple) in enumerate(industry_list):
			if ind_tuple[0] == '':
				blank_industries_list.append(counter)
		for blank in blank_industries_list:
			industry_list.pop(blank)
	return industry_list

def get_positions(user_id):
	print user_id
	return execute_query("select mashup_work_info.position, count(mashup_work_info.position) from mashup_connection_profile, mashup_work_info where mashup_work_info.connection_profile_id  = mashup_connection_profile.id and  mashup_connection_profile.user_id = %s group by mashup_work_info.position order by count( mashup_work_info.position) desc" % (user_id))

def execute_query(query):
	cursor = connection.cursor()
	cursor.execute(query)
	return cursor.fetchall()

def index(request):
	if request.user.is_authenticated():
		#Return locations and number of connections in each to display on Google maps API
		location_list = get_locations(request.user.id)[:30]
		num_of_locations = len(location_list)
                try:
                        connection = request.user.connection_profile_set.get(pk=1)
                        merged_profile = get_merged_profile(connection)
                        jobs_dict = get_work_info(connection, merged_profile)[0]

			jobs_list = get_work_info(connection, merged_profile)[1]
                        points = get_points(jobs_list ,jobs_dict)
                except Exception :
                        pass
		#Return two dictionaries for chart APIs, industry_dict first and position_dict as second list element
		industry_list = get_industries(request.user.id)[:10]
		position_list = get_positions(request.user.id)[:10]

		#Get number of connections in each network to display on homepage.
		#Note: This does not work on local django with sqlite. It works on production with MySQL database.
		num_conns_dict = {'facebook': None, 'linkedin': None, 'twitter': None}
		try:
			num_conns_dict["facebook"] = len(request.user.connection_profile_set.filter(source='facebook').distinct('source_id'))
			num_conns_dict["linkedin"] = len(request.user.connection_profile_set.filter(source='linkedin').distinct('source_id'))
			num_conns_dict["twitter"] = len(request.user.connection_profile_set.filter(source='twitter').distinct('source_id'))
		except Exception, e:
			msg = str(str(datetime.datetime.now())+' '+str(Exception)+' '+str(e))
			print msg
			logger.warning(msg)

		news_articles_dict_trimmed = {}
		connectionId = ""
		connectionId1 = ""
		try:
			user_facebook_id = request.user.get_profile().source_id
			connectionId1 = request.user.connection_profile_set.get(source_id=user_facebook_id)
			#Get news articles for connection
			[news_articles_urls, news_articles_dict] = get_news_articles(connectionId1)
			#news_articles_dict = get_news_articles(connection)[1]
	
			#Get only first n articles
			for i in range(settings.NUM_NEWS_ARTICLES):
				news_articles_dict_trimmed[news_articles_urls[i]] = news_articles_dict[news_articles_urls[i]]
		except Exception, e:
			print e
			
		connectionId = request.user
		
		#Return app_url along with data
		app_url = settings.APP_URL
                mps = request.user.connection_profile_merged_set.all()

		return render_to_response('mashup/index.html', {'num_friends':len(mps) ,'location_list': location_list, 'num_of_locations': num_of_locations, 'industry_list':industry_list, 'position_list': position_list, 'app_url': app_url, 'num_conns_dict': num_conns_dict, 'news_articles_dict_trimmed': news_articles_dict_trimmed, 'connectionId':connectionId1}, context_instance=RequestContext(request))
	else:
		return HttpResponse("You are not logged in! <a href='/accounts/login/?next=/'>Login</a> | <a href='/accounts/register/'>register</a>")

#Encapsulated functions for get_connection_details function
#If a Connection_Profile_Merged object does not exist for this connection, create one
#@frances
def get_merged_profile(connection):
	merged_profile = []
	if connection.source == 'linkedin':
		merged_profile = Connection_Profile_Merged.objects.filter(li_connection_profile=connection)
	elif connection.source == 'facebook':
		merged_profile = Connection_Profile_Merged.objects.filter(fb_connection_profile=connection)
	elif connection.source == 'twitter':
		merged_profile = Connection_Profile_Merged.objects.filter(tw_connection_profile=connection)
	else:
		merged_profile = []
	return merged_profile

def get_work_info(connection, merged_profile):
	jobs_list = []
	if len(merged_profile):
		#Get work info from linkedin
		if connection.source == 'linkedin':
			jobs_list = connection.work_info_set.all()
			#If no jobs in linkedin profile, try from facebook
			if len(jobs_list)==0:
				if merged_profile[0].fb_connection_profile:
					connection_fb = merged_profile[0].fb_connection_profile
					jobs_list = connection_fb.work_info_set.all()
		elif connection.source == 'facebook':
			if merged_profile[0].li_connection_profile:
				connection_li = merged_profile[0].li_connection_profile
				jobs_list = connection_li.work_info_set.all()
			else:
				jobs_list = connection.work_info_set.all()
		elif connection.source == 'twitter':
			if merged_profile[0].li_connection_profile:
				connection_li = merged_profile[0].li_connection_profile
				jobs_list = connection_li.work_info_set.all()
			else:
				jobs_list = connection.work_info_set.all()
	else:
		#get work info
		jobs_list = connection.work_info_set.all()
	# Printing all companies and industries when viewing a connection's profile
	job_dict = {}
        
	for job in jobs_list:
		job_dict[job] = job.industry
	return [job_dict, jobs_list]

def get_current_industry_and_company(connection, merged_profile):
	current_industry_list = []
	current_company_list = []
	jobs_list = get_work_info(connection, merged_profile)[1]
	#Get current industry for Google search
	for job in jobs_list:
		if job.isCurrent == True:
			current_industry_list.append(job.industry)
			current_company_list.append(job.company_name)
	return [current_industry_list, current_company_list]

def get_school_names(connection, merged_profile):
	school_names = []
	educational_institutions_list = []
	if len(merged_profile):
		# Getting all schools from facebook
		if connection.source == 'linkedin':
			if merged_profile[0].fb_connection_profile:
				connection_fb = merged_profile[0].fb_connection_profile
				educational_institutions_list = connection_fb.education_info_set.all()
				if len(educational_institutions_list) == 0:
					educational_institutions_list = connection.education_info_set.all()
		elif connection.source == 'facebook':
			educational_institutions_list = connection.education_info_set.all()
			if len(educational_institutions_list) == 0:
				if merged_profile[0].li_connection_profile:
					connection_li = merged_profile[0].li_connection_profile
					educational_institutions_list = connection_li.education_info_set.all()
	else:
		# Printing all schools when viewing a connection's profile
		educational_institutions_list = connection.education_info_set.all()
	#create list school_names holding text names of schools and return it
	for school in educational_institutions_list:
		school_names.append(school.name)
	return school_names

def get_events(connection, merged_profile):
	events_list = []
	if len(merged_profile):
		# Get Events connection is attending from facebook
		if connection.source == 'linkedin':
			if merged_profile[0].fb_connection_profile:
				connection_fb = merged_profile[0].fb_connection_profile
				events_list = connection_fb.event_set.all()
		else:
			events_list = connection.event_set.all()
	else:
		# Get Events connection is attending
		events_list = connection.event_set.all()
	return events_list

def get_likes(connection, merged_profile):
	likes_list = []
	if len(merged_profile):
		likes_list = []
		# Get connection's likes
		if connection.source == 'linkedin':
			if merged_profile[0].fb_connection_profile:
				connection_fb = merged_profile[0].fb_connection_profile
				likes_list = connection_fb.connection_otherinfo_set.filter(info_type='like')
		elif connection.source == 'facebook':
			likes_list = connection.connection_otherinfo_set.filter(info_type='like')
	else:
		# Get Likes
		likes_list = connection.connection_otherinfo_set.filter(info_type='like')


	return likes_list

def get_likes_names(connection, merged_profile):
	likes_list = []
	if len(merged_profile):
		likes_list = []
		# Get connection's likes
		if connection.source == 'linkedin':
			if merged_profile[0].fb_connection_profile:
				connection_fb = merged_profile[0].fb_connection_profile
				likes_list = connection_fb.connection_otherinfo_set.filter(info_type='like')
		elif connection.source == 'facebook':
			likes_list = connection.connection_otherinfo_set.filter(info_type='like')
	else:
		# Get Likes
		likes_list = connection.connection_otherinfo_set.filter(info_type='like')

	likes_names_list = []
	for like_i in likes_list:
		likes_names_list.append(like_i.name)
	return likes_names_list

#TODO: Bug in get_picture_url - Doesn't show FB pic if no LI pic.
def get_picture_url(connection, merged_profile):
	try:
		picture_url = ''
		if len(merged_profile) == 0:
			picture_url = connection.picture
		else:
			#Prioritize showing pic in following order: LI, FB, TW
			if merged_profile[0].li_connection_profile is not None:
				connection_li = merged_profile[0].li_connection_profile
				picture_url = connection_li.picture
			elif merged_profile[0].fb_connection_profile is not None:
				connection_fb = merged_profile[0].fb_connection_profile
				picture_url = connection_fb.picture
			elif merged_profile[0].tw_connection_profile is not None:
				connection_tw = merged_profile[0].tw_connection_profile
				picture_url = connection_tw.picture
		return picture_url
	except Exception, e:
		print Exception, e
		logger.error(e)

def get_conn_source(connection, merged_profile):
	try:
		source = ''
		if len(merged_profile) == 0:
			source = connection.source
		else:
			if merged_profile[0].fb_connection_profile is not None:
				source += 'Facebook '
			if merged_profile[0].li_connection_profile is not None:
				source += 'Linkedin '
			if merged_profile[0].tw_connection_profile is not None:
				source += 'Twitter '
		return source
	except Exception, e:
		print Exception, e
		logger.error(e)

def get_groups(connection, merged_profile):
	groups_list = []
	if len(merged_profile):
		# Show groups from both Facebook and Linkedin
		if merged_profile[0].fb_connection_profile:
			connection_fb = merged_profile[0].fb_connection_profile
			groups_list.extend(connection_fb.group_set.all())
		if merged_profile[0].li_connection_profile:
			connection_li = merged_profile[0].li_connection_profile
			groups_list.extend(connection_li.group_set.all())
	else:
		# Printing all schools when viewing a connection's profile
		groups_list = connection.group_set.all()
	return groups_list

def get_connection_details(request, connection_id):
	if request.user.is_authenticated():
		try:
			connection = request.user.connection_profile_set.get(pk=connection_id)
			request.session["rank"] = int(request.GET["rank"])

			#Get pointers of the same profile on facebook/linkedin/twitter from Connection_Profile_Merged
			merged_profile = get_merged_profile(connection)

			source = get_conn_source(connection, merged_profile)

			#TODO Display interests and use DBPedia to display blurb about interests
#			company_row = execute_sparql(company_sparql(company_name))
#			interests = execute_sparql(interest_sparql(connection.interests))
#			interest_2_row = execute_sparql(interest_sparql(connection.interest_2))

			#Get picture url
			picture_url = get_picture_url(connection, merged_profile)
			
			#Get work info from linkedin or facebook
			jobs_dict = get_work_info(connection, merged_profile)[0]

			jobs_list = get_work_info(connection, merged_profile)[1]
			#Get current industry
			current_industry_and_company_list = get_current_industry_and_company(connection, merged_profile)
			current_industry_list = current_industry_and_company_list[0]
			current_company_list = current_industry_and_company_list[1]
			if len(current_industry_list)>0:
				current_industry = current_industry_list[0]
			else:
				current_industry = ''
			if len(current_company_list)>0:
				current_company = current_company_list[0]
			else:
				current_company = ''

			#Get school names
			schools_names = get_school_names(connection, merged_profile)

			#Get event names
			events_list = get_events(connection, merged_profile)

			#Get likes
			likes_list = get_likes(connection, merged_profile)

			#get blurb about each like and store in likes dictionary
			likes_dict = dict()
			for like in likes_list:
				#result = execute_sparql(interest_sparql(like.name))
				result = None
				if result is None:
					abstract = "No info from Wikipedia"
				else:
					abstract = result['abstract']['value']
				likes_dict[like] = abstract

			#Get groups
			groups_list = get_groups(connection, merged_profile)

			#Get news articles for connection
			[news_articles_urls, news_articles_dict] = get_news_articles(connection)
			#news_articles_dict = get_news_articles(connection)[1]
			news_articles_dict_trimmed = {}
			#Get only first n articles
			context = []
			text = ""
			for i in range(min(settings.NUM_NEWS_ARTICLES,len(news_articles_urls))):
				news_articles_dict_trimmed[news_articles_urls[i]] = news_articles_dict[news_articles_urls[i]]
			for like_i in likes_list:
				text = text + like_i.name + " "
			mps = request.user.connection_profile_merged_set.all()
			points = get_points(jobs_list ,jobs_dict)
			picture_url = picture_url[picture_url.index("u'http")+2:picture_url.index(".jpg")+4]
			#return render_to_response('mashup/connection_detail.html', {'connection': connection, 'jobs_dict': jobs_dict, 'likes_dict': likes_dict, 'current_industry': current_industry, 'current_company': current_company, 'schools_names': schools_names, 'events_list': events_list, 'likes_list': likes_list, 'source': source, 'picture_url': picture_url, 'groups_list': groups_list}, context_instance=RequestContext(request))
			return render_to_response('mashup/connection_detail.html', {'connection': connection, 'news_articles_dict_trimmed': news_articles_dict_trimmed, 'jobs_dict': jobs_dict,'jobs_list': jobs_list, 'likes_dict': likes_dict, 'current_industry': current_industry, 'current_company': current_company, 'schools_names': schools_names, 'events_list': events_list, 'likes_list': likes_list, 'source': source, 'picture_url': picture_url, 'groups_list': groups_list, 'context':context, 'num_friends':len(mps), 'points':points}, context_instance=RequestContext(request))

		except Connection_Profile.DoesNotExist, e:
			msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
			print msg
			logger.error(msg)
			return HttpResponse("No such connection exists in your network. <a href='/"+settings.APP_URL+"'>Home</a>")
		except Exception, e:
			msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
			print msg
			logger.error(msg)
	else:
		return HttpResponse("You are not logged in! <a href='/admin/'>Login</a>")

#returns non-zero values of number of connections in all industries and positions to html page
#Note: does not account for semantic differences of the same position and industry

def get_chart_info(user):
	#create empty dictionaries
	industry_dict = dict()
	position_dict = dict()
	industry_dict_filtered = dict()
	position_dict_filtered = dict()

	conns_all = user.connection_profile_set.all() #list of all connection profile objects
	conns = [] #list of connection_profile objects that have corresponding merged profile

	merged_conns = user.connection_profile_merged_set.all()
	li_conns_all = user.connection_profile_set.filter(source = "linkedin", degree_of_separation=1)  #list of all linkedin connection profile objects
	li_conns = [] #list of linkedin connection_profile objects that have corresponding merged profile


	#initialize dictionary with 0 values for each industry, position
	#only take it from linkedin
	for w in Work_Info.objects.all():
		if w.industry != None and w.connection_profile.source == "linkedin":
			industry_name = w.industry
			if industry_name not in industry_dict:
				industry_dict[industry_name] = 0
		if w.position != None and w.connection_profile.source == "linkedin":
			position_name = w.position
			if position_name not in position_dict:
				position_dict[position_name] = 0


	industry_dict_keys = industry_dict.keys()
	position_dict_keys = position_dict.keys()
	print "# industry keys = ", len(industry_dict_keys)
	print "# position keys = ", len(position_dict_keys)

	for mc in merged_conns:
		#connection = request.user.connection_profile_set.get(pk=connection_id)

		fb_cp = mc.fb_connection_profile #corresponding facebook connection profile
		li_cp = mc.li_connection_profile #corresponding linked in connection profile

		#add industries and positions from fb and li connection profiles to a set so there are no duplicates
		fb_work_infos = fb_cp.work_info_set.all()
		li_work_infos = li_cp.work_info_set.all()

		for wi in fb_work_infos:
			for ik in industry_dict_keys:
				if wi.industry != None:
					if wi.industry.upper().strip() in ik.upper().strip() or ik.upper().strip() in wi.industry.upper().strip():
						industry_dict[ik] = industry_dict[ik] + 1
			for pk in position_dict_keys:
				if wi.position != None:
					if wi.position.upper().strip() in pk.upper().strip() or pk.upper().strip() in wi.position.upper().strip():
						position_dict[pk] = position_dict[pk] + 1

		for wi in li_work_infos:
			for ik in industry_dict_keys:
				if wi.industry != None:
					if wi.industry.upper().strip() in ik.upper().strip() or ik.upper().strip() in wi.industry.upper().strip():
						industry_dict[ik] = industry_dict[ik] + 1
			for pk in position_dict_keys:
				if wi.position != None:
					if wi.position.upper().strip() in pk.upper().strip() or pk.upper().strip() in wi.position.upper().strip():
						position_dict[pk] = position_dict[pk] + 1

	for c in conns_all:
		if c not in conns:
			c_work_infos = c.work_info_set.all()
			for wi in c_work_infos:
				for ik in industry_dict_keys:
					if wi.industry != None:
						if wi.industry.upper().strip() in ik.upper().strip() or ik.upper().strip() in wi.industry.upper().strip():
							industry_dict[ik] = industry_dict[ik] + 1
				for pk in position_dict_keys:
					if wi.position != None:
						if wi.position.upper().strip() in pk.upper().strip() or pk.upper().strip() in wi.position.upper().strip():
							position_dict[pk] = position_dict[pk] + 1


	#filter out non-zero number values in dictionary
	for industry_name in industry_dict:
		num_conns = industry_dict[industry_name]
		if num_conns != 0:
			industry_dict_filtered[industry_name] = num_conns
			print "(industry =", industry_name, ", ", industry_dict[industry_name], ")"

	#print out contents of position_dict
	for position_name in position_dict:
		num_conns = position_dict[position_name]
		if num_conns != 0:
			position_dict_filtered[position_name] = num_conns
			print "(position = ", position_name, ", ", position_dict[position_name], ")"

		#only return industries, positions that have top 10 most connections
		# 	print [k for v, k in sorted(((v, k) for k, v in industry_dict.items()), reverse = True)]
		# 	print [k for v, k in sorted(((v, k) for k, v in position_dict.items()))]

	count = 0
	for industry in [k for v, k in sorted(((v, k) for k, v in industry_dict.items()), reverse = True)]:
		if count < 5:
			print "%s: %s" % (industry, industry_dict[industry])
			#industry_dict_filtered[position_name] = industry_dict[industry]
			count+=1
		else:
			break
	count = 0
	for position in [k for v, k in sorted(((v, k) for k, v in position_dict.items()), reverse = True)]:
		if count <5:
			print "%s: %s" % (position, position_dict[position])
			#position_dict_filtered[position_name] = position_dict[position]
			count+=1
		else:
			break

	return_list = [industry_dict_filtered, position_dict_filtered]

	return return_list

#@fzhang
#returns the number of connections in all locations in the google map
#Note: locations are generated from standardized linked in locations, not facebook
def get_num_conns_in_all_areas(user):
	#create dictionary for charts
	location_dict = dict()  #key = location name, #value = number of connections living in location

	merged_conns = user.connection_profile_merged_set.all()
	li_conns_all = user.connection_profile_set.filter(source = "linkedin", degree_of_separation=1)  #list of all linkedin connection profile objects
	li_conns = [] #list of linkedin connection_profile objects that have corresponding merged profile

	#populate location dictionary keys with all location names from linkedin connections
	#start by iterating through all merged connection profiles to prevent double counting
	for mc in merged_conns:
		li_cp = mc.li_connection_profile

		if li_cp != None:
			li_conns.append(li_cp)
			if li_cp.current_location != None:
				location_name = sb_sql.strip_location(li_cp.current_location.name.strip())  #only get location names from linked in categories since they are standardized
				if location_name not in location_dict: #key does not exist -> add key to dict
					location_dict[location_name] = 0
				#print "location = ", location_name

	for lc in li_conns_all:
		if lc not in li_conns:
			if lc.current_location != None:
				location_name = sb_sql.strip_location(lc.current_location.name.strip())  #only get location names from linked in categories since they are standardized
				if location_name not in location_dict: #key does not exist -> add key to dict
					location_dict[location_name] = 0

	for location_name in location_dict: #iterate through all location names in dictionary
		num = get_num_conns_in_area(user, location_name)
		location_dict[location_name] = num
		print "(", location_name, ", num = ", num, ")"

	return location_dict

#@fzhang
#helper function for get_num_conns_in_all_areas used to draw the google map visualization
#returns number of connections in the location given
def get_num_conns_in_area(user, location):
	num = 0
	location.strip()
	merged_conns = user.connection_profile_merged_set.all() #list of all connection_profile_merged objects
	conns_all = user.connection_profile_set.all() #list of all connection profile objects
	conns = [] #list of connection_profile objects that have corresponding merged profile

	fb_match = False
	li_match = False
	conn_match = False

	#iterate through all merged connections first to prevent double counting
	for mc in merged_conns:

		fb_cp = mc.fb_connection_profile #corresponding facebook connection profile
		li_cp = mc.li_connection_profile #corresponding linked in connection profile


		#location match for facebook
		if fb_cp != None:
			conns.append(fb_cp)
			if fb_cp.current_location != None:
				fb_match = location.upper() in fb_cp.current_location.name.upper() or fb_cp.current_location.name.upper() in location.upper()
		else:
			fb_match = False

		#location match for linked in
		if li_cp != None:
			conns.append(li_cp)
			if li_cp.current_location != None:
				li_match = location.upper() in li_cp.current_location.name.upper() or li_cp.current_location.name.upper() in location.upper()
		else:
			li_match = False

		#location match for linkedin
		if fb_match or li_match:
			num = num+1

	#iterate through all singular connections
	for c in conns_all:
		if c not in conns and c.current_location != None:
			conn_match = location.upper() in c.current_location.name.upper() or c.current_location.name.upper() in location.upper()
		if conn_match:
			num = num + 1

	#print "number of connections in ",location, " = ", num
	return num

#@fzhang
#used to display value of emotional accessibility
def get_emotional_score(request, connection_id):
	score = 0; #get from database!!
	return render_to_response('mashup/connection_details.html', {'emotional_score': score})


#used to display value of physical accessibility
def get_physical_score(request, connection_id):
	score = 0; #get from database!
	return render_to_response('mashup/connection_details.html', {'physical_score': score})


def company_html(sparql_results):

	print "Content-type: text/html"
	print """
			<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
			<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
			<head>
					<link rel="stylesheet" type="text/css" href="http://web.mit.edu/~lkagal/Public/table.css" />
					<meta http-equiv="content-type" content="text/html; charset=utf-8" />
					<title>Example of Use of SPARQLWrapper within CGI</title>
			</head>
			<body>
	"""

	print "<table  id='customers' width='60%'>  <col width = '20%' /> <col width='20%' /> <col width='30%' /> <col width='30%' />"
	print " <tr> <th>Name </th> <th>Company</th> <th>Industry</th> <th>Key Person</th> <th>Company Info</th></tr>"

	for info in sparql_results["results"]["bindings"]:
		print "<tr>"
		print "<td>", info["company"], "</td>"
		print "<td>", info["industry"], "</td>"
		print "<td>", info["keyperson"], "</td>"
		print "<td>", info["thumbnail"], "</td>"
		print "<td>", info["abstract"], "</td>"
		print "<td>"
		try:
			print "done"
		except Exception, e:
			print " "
		print "</td>"
		print "</tr>"
	print "</table>"
	print "</body></html>"

	return


def get_recommendations(request): #Weights

	loc_input = request.POST['location'].upper()
	comp_input = request.POST['company'].upper()
	ind_input = request.POST['industry'].upper()

	#first pass
	comp_weight = 1
	loc_weight = 6 * comp_weight
	ind_weight = 8 * comp_weight

	#second pass
#	fb_weight = 1
#	linkedIn_weight = 2 * fb_weight
#	linkedIn_fb_weight = 4 * fb_weight

	#third pass - degree of separation
	#get inputs - company, location, industry
	#comp_input = "Goldman Sachs".upper()
	#loc_input = "New York".upper()
	#ind_input = "Finance".upper()

	response = ""
	count = 0
	connection_scores = []

	for con in request.user.connection_set.all():
		count += 1
		score = 0
		#preprocessing
		try:
			loc = str(con.location).strip().upper()
#			src = str(con.source).strip().upper()
			comp1 = str(con.company_1).strip().upper()
			comp2 = str(con.company_2).strip().upper()
			comp3 = str(con.company_3).strip().upper()
			comp4 = str(con.company_4).strip().upper()

			ind1 = str(con.industry_1).strip().upper()
			ind2 = str(con.industry_2).strip().upper()
			ind3 = str(con.industry_3).strip().upper()
			ind4 = str(con.industry_4).strip().upper()

			#check industry match - need to get the field
			if ind1 != "" and (ind_input in ind1 or ind1 in ind_input):
				score += 4*ind_weight
			elif ind2 != "" and (ind_input in ind2 or ind2 in ind_input):
				score += 3*ind_weight
			elif ind3 != "" and (ind_input in ind3 or ind3 in ind_input):
				score += 2*ind_weight
			elif ind4 != "" and (ind_input in ind4 or ind4 in ind_input):
				score += 1*ind_weight

			#check location match - CHECK CONTAINS METHOD

			if loc != "" and loc_input in loc:
				score += loc_weight
				#response += "LOCATION MATCH: " + str(con) + " " + str(con.location)

			#check company match
			if comp1 != "" and (comp_input in comp1 or comp1 in comp_input):
				score += 4*comp_weight
				#response += "COMPANY MATCH: index = " + str(count) + ", con = " + str(con) +  " co: " + str(con.company_1)
			elif comp2 != "" and (comp_input in comp2 or comp2 in comp_input):
				score += 3*comp_weight
			elif comp3 != "" and (comp_input in comp3 or comp3 in comp_input):
				score += 2*comp_weight
			elif comp4 != "" and (comp_input in comp4 or comp4 in comp_input):
				score += 1*comp_weight


		except Exception: #check for Null, etc.
				continue
		if score > 0: connection_scores.append([con,score])
		print "(con, loc, comp, ind, index, score) = (", con, ", ", loc, ", ", comp1, ", ", ind1, ", ", count, ", ", score, ")"

	#sort connections by score - return top 10 - first pass
	first_pass = sorted(connection_scores, key=lambda a: -a[1])

	#second pass
	for tup in first_pass[:10]:
		src = str(tup[0].source).strip().upper()
		if src == "LINKEDIN": tup.append(2) #rank
		elif src == "FACEBOOK": tup.append(1)
		else: tup.append(0)
	second_pass = sorted(first_pass[:10], key=lambda a: -a[2])

	connections_sorted = []

	#third pass
	for tup in second_pass:
		con = tup[0]
		dos = str(con.degree_of_separation).strip()
		if dos != "":
			if dos == str(1): tup.append(3) #rank
			elif dos == str(2): tup.append(2)
			elif dos == str(3): tup.append(1)
		else:
			tup.append(0)

	third_pass = sorted(second_pass, key=lambda a: -a[3])

	#print connections in order
	response += "Connections in order: "
	for tup in third_pass:
		con = tup[0]
#		name = str(con.first_name) + " " + str(con.last_name)
#		location = str(con.location)
#		company = str(con.company_1)
#		industry = str(con.industry_1)
		connections_sorted.append(con)

	for con in connections_sorted:
		response+=str(con)+",  loc: "+str(con.location) + ", ind: " + str(con.industry_1) + ", co: " + str(con.company_1)

	#return HttpResponse(response)
	#user = request.user
	return render_to_response('mashup/recs.html', {'connections_sorted': connections_sorted, 'user': request.user}, context_instance=RequestContext(request))

def filter(request):
	try:
		if request.user.is_authenticated():

			#if POST request has parameters, then put them in session. Else assume that they are already in.
			if (request.POST.get("location", None) is not None) or  (request.POST.get("company") is not None) or (request.POST.get("industry") is not None):
				request.session["session_location"] = request.POST["location"]
				request.session["session_company"] = request.POST["company"]
				request.session["session_industry"] = request.POST["industry"]
				request.session["session_interest"] = request.POST["interest"]
				request.session["session_school"] = request.POST["school"]
				request.session["session_characteristic"] = request.POST["characteristic"]
				# print "Parameters for LinkedIn From POST request: ", request.POST["location"], request.POST["company"], request.POST["industry"]

	#		#check if the authentication tokens are in session, if not call oath handshake
	#		if sb_linkedin.is_linkedin_authorized(request) is False:
	#			#store this url in session
	#			# print "Storing RedirectURL after OAuth: ", request.path
	#			request.session["session_linkedin_oauth_callingurl"] = "http://" + request.get_host()  + request.path
	#
	#			#redirect to HTTP oath step1
	#			return HttpResponseRedirect(sb_linkedin.LINKEDIN_OAUTH_STEP1_URL)
	#
	#		# Load settings.LINKEDIN_SEARCH_COUNT nos. of 2nd degree LinkedIn connections.
	#		sb_linkedin.load_linkedin(request, "2") 

			# Doing list(set()) to remove duplicates
			#TODO - fix this filter. parameterize based on number of inputs. For now, workaround is to filter by company and location.
			connection_list = list(set(request.user.connection_profile_set.filter(current_location__name__icontains=request.session.get('session_location'), work_info__industry__icontains=request.session.get('session_industry'), education_info__name__icontains=request.session.get('session_school'), work_info__company_name__icontains=request.session.get('session_company'), connection_otherinfo__name__icontains=request.session.get('session_interest'))))

	#		print "in filter:", request.session.get('session_location'), request.session.get('session_company'), request.session.get('session_industry')
	#		print connection_list


			if str(request.session["session_characteristic"]) == 'entrepreneurial':
				connection_list = SB_sort_bu(request,connection_list)[:settings.NO_SEARCH_RESULTS]
			else:
				connection_list = SB_sort(request,connection_list)[:settings.NO_SEARCH_RESULTS] # Load first settings.NO_SEARCH_RESULTS
			#Remove duplicate connections with the same first_name and last_name
			connection_list = remove_duplicates(connection_list)

			#return main app_url
			app_url = settings.APP_URL
			mps = request.user.connection_profile_merged_set.all() 
			for connection in connection_list:
				try:
					connection.picture = connection.picture[connection.picture.index("u'http")+2:connection.picture.index(".jpg")+4]
				except:
					pass
			return render_to_response('mashup/filter.html', {'connection_list': connection_list, 'app_url': app_url, 'num_friends':len(mps)}, context_instance=RequestContext(request))
		else:
			return HttpResponse("You are not logged in! <a href='/accounts/login/?next=/'>Login</a> | <a href='/accounts/register/'>register</a>")
	except Exception, e:
		msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
		print msg
		logger.error(msg)
		return HttpResponse("Please load your facebook network before searching. <a href='/'>Home</a>")

def show_connections(request):
	mps = request.user.connection_profile_merged_set.all()
	print "****************len(mps)", len(mps)
	#return main app_url
	app_url = settings.APP_URL
	print mps[0].picture_fb
	return render_to_response('mashup/myconnections.html', {'merged_connection_list':mps, 'app_url': app_url, 'num_friends':len(mps)}, context_instance=RequestContext(request))

# Function to remove duplicates in connection list
def remove_duplicates(connection_list):
	temp_conn_list = list(connection_list)
	fn_ln_tuple_list = []
	indices_to_remove_from_conn_list = []
	for idx, conn in enumerate(connection_list):
		name_tuple = (conn.first_name, conn.last_name)
		if name_tuple not in fn_ln_tuple_list:
			fn_ln_tuple_list.append(name_tuple)
		else:
			indices_to_remove_from_conn_list.append(idx)
	if len(indices_to_remove_from_conn_list) > 0:
		indices_to_remove_from_conn_list.reverse()
		for idx in indices_to_remove_from_conn_list:
			del temp_conn_list[idx]
	return temp_conn_list

# Function to get time difference between now and last save date
# def get_timedelta(c_profile):
	# now = datetime.datetime.now()
	# save_time = c_profile.last_saved_on
	# delta = now - save_time
	# return delta


def translate_to_buckets(merged_profile):
	object_exists = []
	object_exists = RecommendationBucket.objects.filter(merged_profile=merged_profile)
	if len(object_exists) == 0:
		rec_bucket = RecommendationBucket(merged_profile=merged_profile)
	else:
		rec_bucket = RecommendationBucket.objects.get(merged_profile=merged_profile)
	#Store each current location from every separate profile
	rec_bucket.locations = merged_profile.current_location.name

	#Store each university name from every separate profile
	educations_list = []
	for education in merged_profile.education_info_set.all():
		educations_list.append(education.name)
		educations_list.append(";")
	rec_bucket.educations = ''.join(educations_list)

	#Store each work industry from every separate profile
	industry_list = []
	for work in merged_profile.work_info_set.all():
		if work.industry not in industry_list:
			industry_list.append(work.industry)
			industry_list.append(";")
	rec_bucket.industries = ''.join(industry_list)

	#Store skills from linkedin into skills
	rec_bucket.skills = merged_profile.skills

	#Store interests from each profile into interests
	interests_dict = {}
	for interest in merged_profile.interests.all():
		if interest.category in interests_dict.keys():
			interests_dict[interest.category].append(interest.name)
		else:
			interests_dict[interest.category] = [interest.name]

	#Save Music into RecommendationBucket model
	if "Music" in interests_dict.keys():
		music_list = []
		for interest in interests_dict["Music"]:
			music_list.append(interest)
		rec_bucket.music = ''.join(music_list)

	#Save Musician/band into RecommendationBucket model
	if "Musician/band" in interests_dict.keys():
		music_list = []
		for interest in interests_dict["Musician/band"]:
			music_list.append(interest)
		rec_bucket.musician_bands = ''.join(music_list)

		#Save RecommendationBucket
	rec_bucket.save()
def SB_sort(request,connection_list):
	print "sbsort Size of conection list:", len(connection_list),"\n"

	user_facebook_id = merging.get_or_create_user_profile(request).source_id
	#TODO - user_facebook_id is only set when we load facebook data. Need to set this value as part of the login
	user_conn_profile = request.user.connection_profile_set.get(source_id=user_facebook_id)
	user_merged_profile = get_merged_profile(user_conn_profile)
	user_events_names = get_events(user_conn_profile, user_merged_profile)
	beta_events = 10
	beta_likes = 10

#	print "Location: "
#	print user_conn_profile.current_location
#	print "\n"
#	print "EA: "
#	print user_conn_profile.emotional_accessibility
#	print "\n"
#	print "PA: "
#	print user_conn_profile.physical_accessibility
#	print "\n"
#	print "TA: "
#	print user_conn_profile.total_accessibility
#	print "\n"



	for fp in connection_list:
		num_common_likes = ComputeLikes(request.user,fp)
		print "Common Likes: "
		print num_common_likes
		print "\n"
		emotional_access = 50 + ComputeEvents(request.user,fp)*beta_events* + ComputeLikes(request.user,fp)*beta_likes
		physical_access = 0
		print "User current locaton:"
		print user_conn_profile.current_location
		print "\n"
		print "Friend current locaton:"
		print fp.current_location
		print "\n"
		if user_conn_profile.current_location == fp.current_location:
			physical_access = 25
		physical_access = physical_access + (4- fp.degree_of_separation)*25
		fp.emotional_accessibility = emotional_access
		fp.physical_accessibility = physical_access
		fp.total_accessibility = emotional_access + physical_access
		fp.save()
		print "Emotional: "
		print fp.emotional_accessibility
		print "\n"
		print "Physical: "
		print fp.physical_accessibility
		print "\n"
	connection_list = sorted(connection_list, key=attrgetter('total_accessibility'),reverse=True)
	return connection_list


def ComputeEvents(user,fp):

	user_facebook_id = user.get_profile().source_id
	user_conn_profile = user.connection_profile_set.get(source_id=user_facebook_id)
	user_merged_profile = get_merged_profile(user_conn_profile)
	user_events_names = get_events(user_conn_profile, user_merged_profile)

#	print "Usr events: "
#	print user_events_names
#	print "\n"
	fp_merged_profile = get_merged_profile(fp)
	fp_events_names = get_events(fp, fp_merged_profile)
#	print "Friend events: "
#	print fp_events_names
#	print "\n"

	fp_events_vector = fp_events_names
	user_events_vector = user_events_names

	common_events = list(set(fp_events_vector) & set(user_events_vector))
	numEvents = len(common_events) + 1
#	print "NumEvents : "
#	print numEvents
#	print "\n"
	return numEvents

def ComputeLikes(user,fp):
	user_facebook_id = user.get_profile().source_id
	user_conn_profile = user.connection_profile_set.get(source_id=user_facebook_id)
	user_merged_profile = get_merged_profile(user_conn_profile)
	user_likes_names = get_likes_names(user_conn_profile, user_merged_profile)
	print "Usr likes: "
	print user_likes_names
	print "\n"
	fp_merged_profile = get_merged_profile(fp)
	fp_likes_names = get_likes_names(fp, fp_merged_profile)
	print "Friend likes: "
	print fp_likes_names
	print "\n"

	fp_likes_vector = fp_likes_names
	user_likes_vector = user_likes_names
	common_likes = list(set(fp_likes_vector) & set(user_likes_vector))
	print "common likes = ", common_likes
	numLikes = len(common_likes) + 1
#	print "NumLikes : "
#	print numLikes
#	print "\n"
	return numLikes

def get_news_articles(fbp):
	fbp_merged_profile = get_merged_profile(fbp)
	fbp_likes_names = get_likes_names(fbp, fbp_merged_profile)
	
	#Get the news articles data
	infile = open( settings.NEWS_FILE_PATH+"urls_data.txt", "r" )
	na_data = []
	for line in infile:
    		na_data.append( line )
	na_titles = {}
	na_urls = []
		
	for like_i in fbp_likes_names:
		for line in na_data:
			line2 = line.rstrip("\n")
			values = line2.split('@')
			if like_i == values[0]:
				na_urls.append(values[2])
				na_titles[values[2]] = like_i

	return [na_urls, na_titles]


def SB_sort_bu(user,connection_list):
	founders_connection_list = []
	for fp in connection_list:
		fp_merged_profile = get_merged_profile(fp)
		#job_list = fp.work_info_set.all()
		job_list = get_all_jobs(fp,fp_merged_profile)
		for jobc in  job_list:
			if jobc == 'Founder':
				founders_connection_list.append(fp)
			if jobc == 'Co-Founder':
				founders_connection_list.append(fp)
			if jobc == 'Co-Founder & President':
				founders_connection_list.append(fp)
			if jobc == 'CEO':
				founders_connection_list.append(fp)
			if jobc == 'COO':
				founders_connection_list.append(fp)
			if jobc == 'President':
				founders_connection_list.append(fp)
			if jobc == 'Chairman':
				founders_connection_list.append(fp)
			if jobc == 'Venture':
				founders_connection_list.append(fp)
			if jobc == 'CFO':
				founders_connection_list.append(fp)
	founders_connection_list = list(set(founders_connection_list))
	sortedFoundersList = SB_sort(user,founders_connection_list)
	return sortedFoundersList



#Function to save user rating of searches per user
def save_rating(request, connection_id):
	if request.user.is_authenticated():
		try:
			#get search parameters from session
			session_location = request.session["session_location"]
			session_company = request.session["session_company"]
			session_industry = request.session["session_industry"]
			session_interests = request.session["session_interest"]
			user_search_rating = request.POST["rating"]
			user_rating_comment = request.POST["comment"]
			connection = request.user.connection_profile_set.get(pk=connection_id)
			rank = request.session["rank"]
			search_parameters = 'location='+session_location+';industry='+session_industry+';company='+session_company+';interests='+session_interests+';'
			rating = SearchConnectionRating(user=request.user, search_parameters=search_parameters, connection_profile=connection, connection_profile_rank=rank, rating=user_search_rating, rating_comment=user_rating_comment)
			rating.save()

			return render_to_response('mashup/rating.html', {}, context_instance=RequestContext(request))
		except ValueError, e:
			msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
			print msg
			logger.error(msg)
			return HttpResponse("Please only use integers for rating. <a href='javascript:window.close();'>Close Window</a>")
		except Exception, e:
			msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
			print msg
			logger.error(msg)
			return HttpResponse("We couldn't save the rating. No worries and thanks, please continue browsing. <a href='javascript:window.close();'>Close Window</a>")
	else:
		return HttpResponse("You are not logged in! <a href='/accounts/login/?next=/'>Login</a> | <a href='/accounts/register/'>register</a>")

#@fzhang: returns an unsorted list of merged profile connections with similar interests
def interest_search(user, interest):
	merged_conns = user.connection_profile_merged_set.all()
	matches = []

	for mc in merged_conns:
		fp = mc.fb_connection_profile
		interest_list = get_likes(fp, mc)
		interest_names = []
		for i in interest_list:
			if interest.strip().lower() in i.name.strip().lower() or i.name.strip().lower() in interest.strip().lower():
				matches.append(mc)

	return matches

def createUserJSON(request):
	conn_pf_list = request.user.connection_profile_set.all()
	user_sourceid = request.user.get_profile().source_id
	user_cp = conn_pf_list.filter(source_id=user_sourceid)[0]
	mp = get_merged_profile(user_cp)[0]

	pfs = []
	if mp.fb_connection_profile is not None:
		pfs.append(mp.fb_connection_profile)
	if mp.li_connection_profile is not None:
		pfs.append(mp.li_connection_profile)
	if mp.tw_connection_profile is not None:
		pfs.append(mp.tw_connection_profile)

	data = []
	for pf in pfs:
		profile_dict = {'website': pf.website,
						'first_name': smart_str(pf.first_name),
						'last_name': smart_str(pf.last_name),
						'username': pf.username,
						'source': pf.source, 'source_id': pf.source_id,
						'created_on': str(pf.created_on),
						'last_saved_on': str(pf.last_saved_on),
						'picture': pf.picture,
						'profile_url': pf.profile_url,
						'locale': pf.locale,
						'significant_other_id': pf.significant_other_id,
						'picture': pf.picture,
						'hometown_location': pf.hometown_location,
						'title': pf.title,
						}
		#check if current_location exists, add to dictionary
		if pf.current_location:
			profile_dict['current_location'] = pf.current_location.name
		#create and add education list
		#TODO: Bug in parsing facebook. Parsing creates multiple education_info objects if you reload facebook friends. Dict below showing multiple educations with same name and year.
		education_list = []
#		education_dict = {}
		for education in pf.education_info_set.all():
			if education.name:
#				education_dict['name'] = education.name
#				education_dict['year'] = education.year
				education_list.append(education.name)
		profile_dict['education'] = list(set(education_list)) #Doing list(set()) to remove duplicates
		#create and add work list
		work_list = []
		for work in pf.work_info_set.all():
			if work.company_name:
				work_list.append(work.company_name)
		profile_dict['work'] = list(set(work_list)) #Doing list(set()) to remove duplicates

		#interests
		interest_list = []
		for interest in pf.connection_otherinfo_set.all():
			if interest.name:
				interest_list.append(interest.name)
		profile_dict["interests"] = list(set(interest_list))

		#events
		event_list = []
		for event in pf.event_set.all():
			if event.name:
				event_list.append(event.name)
		profile_dict["events"] = list(set(event_list))

		#groups
		group_list = []
		for group in pf.group_set.all():
			if group.name:
				group_list.append(group.name)
		profile_dict["groups"] = list(set(group_list))

		#append fields to dict
		data.append(profile_dict)

	data_dump = simplejson.dumps(data, indent=2, ensure_ascii=False)
	print data_dump
#	data = serializers.serialize("json", pfs)
#
	return render_to_response('mashup/json_output.html', {'data':data_dump})



def createJSON(request):
	merged_pf_list = request.user.connection_profile_merged_set.all()
	conn_pf_list = request.user.connection_profile_set.all()
#
	pfs = set() #use set so that no duplicate connection profile
	#iterate through merged connection profile list so that connection profiles of same user are lumped together in json object
	for mpf in merged_pf_list:
		if mpf.fb_connection_profile != None:
			pfs.add(mpf.fb_connection_profile)
		if mpf.li_connection_profile != None:
			pfs.add(mpf.li_connection_profile)
		if mpf.tw_connection_profile != None:
			pfs.add(mpf.tw_connection_profile)
#
	for cpf in conn_pf_list:
		pfs.add(cpf)

	#create json object out of connection profiles
	#TODO: Need to create a new object that uses selective data from connection profiles, and also replaces object IDs with text
	data = []
	print "# profiles = ", len(pfs)
	for pf in pfs:
		profile_dict = {'website': pf.website,
						'first_name': smart_str(pf.first_name),
						'last_name': smart_str(pf.last_name),
						'username': pf.username,
						'source': pf.source, 'source_id': pf.source_id,
						'created_on': str(pf.created_on),
						'last_saved_on': str(pf.last_saved_on),
						'picture': pf.picture,
						'profile_url': pf.profile_url,
						'locale': pf.locale,
						'total_accessibility': pf.total_accessibility,
						'emotional_accessibility': pf.emotional_accessibility,
						'physical_accessibility': pf.physical_accessibility,
						'significant_other_id': pf.significant_other_id,
						'picture': pf.picture,
						'hometown_location': pf.hometown_location,
						'title': pf.title,
						'proxied_email': pf.proxied_email,
						'degree_of_separation': pf.degree_of_separation,
						'num_connections': pf.num_connections,
						}
		#check if current_location exists, add to dictionary
		if pf.current_location:
			profile_dict['current_location'] = pf.current_location.name
		#create and add education list
		#TODO: Bug in parsing facebook. Parsing creates multiple education_info objects if you reload facebook friends. Dict below showing multiple educations with same name and year.
		education_list = []
#		education_dict = {}
		for education in pf.education_info_set.all():
			if education.name:
#				education_dict['name'] = education.name
#				education_dict['year'] = education.year
				education_list.append(education.name)
		profile_dict['education'] = list(set(education_list)) #Doing list(set()) to remove duplicates
		#create and add work list
		work_list = []
		for work in pf.work_info_set.all():
			if work.company_name:
				work_list.append(work.company_name)
		profile_dict['work'] = list(set(work_list)) #Doing list(set()) to remove duplicates

		#interests
		interest_list = []
		for interest in pf.connection_otherinfo_set.all():
			if interest.name:
				interest_list.append(interest.name)
		profile_dict["interests"] = list(set(interest_list))

		#events
		event_list = []
		for event in pf.event_set.all():
			if event.name:
				event_list.append(event.name)
		profile_dict["events"] = list(set(event_list))

		#groups
		group_list = []
		for group in pf.group_set.all():
			if group.name:
				group_list.append(group.name)
		profile_dict["groups"] = list(set(group_list))

		#append fields to dict
		data.append(profile_dict)

	data_dump = simplejson.dumps(data, indent=2, ensure_ascii=False)
#	print data_dump
#	data = serializers.serialize("json", pfs)
#
	return render_to_response('mashup/json_output.html', {'data':data_dump})
# Hari
def get_points(jobs_list ,jobs_dict):
    exp ,points = 0 ,0
    positions = ['Founder', 'Co-Founder', 'Co-Founder & President', 'CEO', 'COO', 'President', 'Chairman', 'Venture', 'CFO']
    for job in jobs_list:
        if job.position in positions:
            points = points + 50
    for job, ind in jobs_dict.items():
        if job.start_date != None and job.end_date != None :
            exp = exp + (job.end_date - job.start_date) 
    points = points + 10*exp
    return(points)

def add_favourite(request, connection_id):
    append = 1
    if request.user.is_authenticated():
        try:
            try :
                fp = open("{0}_favourites.csv".format(request.user),"r")
            except Exception :
                fp = open("{0}_favourites.csv".format(request.user),"w")
                fp.write("SB_username,SB_user_id,friend_name,SB_friend_id\n")
                fp.close()
            
            connection = request.user.connection_profile_set.get(pk=connection_id)
            SB_username = request.user
            SB_user_id = request.user.id
            friend_name = connection.first_name + connection.last_name
            SB_friend_id = connection_id
            User_facebook_id = request.user.get_profile().source_id
            fp = open("{0}_favourites.csv".format(request.user),"r")
            for line in fp.readlines():
                if SB_friend_id in line and friend_name in line:
                    append = 0
            fp.close()
            if append == 1:
                fp = open("{0}_favourites.csv".format(request.user),"a")
                fp.seek(2)
                fp.write("{0} ,{1} ,{2} ,{3} \n".format(SB_username,SB_user_id,friend_name,SB_friend_id))
                fp.close()
            else :
                pass
            return render_to_response('mashup/favourites.html', {}, context_instance=RequestContext(request))
        except Exception :
            pass
    else:
        return HttpResponse("You are not logged in! <a href='/accounts/login/?next=/'>Login</a> | <a href='/accounts/register/'>register</a>")
    # Hari
