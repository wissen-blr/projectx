from django.http import HttpResponse
from models import *
from django.utils.encoding import smart_str, smart_unicode
import controller
import threading
from django.conf import settings

import logging
logger = logging.getLogger("projectx")

merge_thread_lock = threading.Lock()

# Function to get time difference between now and last save date
def get_timedelta(c_profile):
	now = datetime.datetime.now()
	save_time = c_profile.last_saved_on
	delta = now - save_time
	return delta

#call this whenever an account is loaded
#this merges the connection profile of the user and its connections' profiles with existing connection profiles in the database
def merge(user, source):
	logger.info("Merge starting")
	try:
		cp_list = user.connection_profile_set.filter(source=source)
		NUM_MERGE_THREADS = settings.NUM_MERGE_THREADS
		thread_list = [None]*NUM_MERGE_THREADS

		count = len(cp_list)
		log_msg = "length of cp_list:" + str(count)
		logger.info(log_msg)

		for loopCount in range(0, count/NUM_MERGE_THREADS+1):
			end1 = (loopCount+1)*NUM_MERGE_THREADS
			if end1 > count:
				end = count - loopCount*NUM_MERGE_THREADS
			else:
				end = NUM_MERGE_THREADS

			logger.info("EndPoint="+ str(end))

			for numThreads in range(0,end):
				index = numThreads + loopCount * NUM_MERGE_THREADS
				thread_list[numThreads] = threading.Thread(target=merge_profile, args=(user, cp_list[index]))
				thread_list[numThreads].start()

			#time.sleep(end/5)
			for numThreads2 in range(0,end):
				thread_list[numThreads2].join()

	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in merge user, source") + str(e)
		print msg
		logger.error(msg)


#helper function to merge a connection profile with existing merged connection profiles of the user
#if the user's connection profile is new, then creates a new Connection_Profile_Merged object consisting of just one connection profile pointer
def merge_profile(user, connection_profile):
	log_msg = "merge_profile starting for " + str(connection_profile)
	logger.info(log_msg)

	fn = connection_profile.first_name
	ln = connection_profile.last_name
	mps = user.connection_profile_merged_set.all()
	cpm = None

	matches_mp = user.connection_profile_merged_set.filter(first_name__icontains=fn, last_name__icontains=ln).exclude(source=connection_profile.source)

	#merge object already exists for this connection
	log_msg = "# matches for " + smart_str(fn) + smart_str(ln) + "= " + str(len(matches_mp))
	print log_msg
	logger.info(log_msg)

	try:
		if len(matches_mp) == 1:
			cpm = matches_mp[0]
			log_msg = "found 1 match!!! cpm = " + str(cpm)
			print log_msg
			logger.info(log_msg)

			if cpm.source != connection_profile.source: #new connection profile to be merged
				if connection_profile.source =='facebook':
					cpm.fb_connection_profile = connection_profile
				if connection_profile.source =='linkedin':
					cpm.li_connection_profile = connection_profile
				if connection_profile.source =='twitter':
					cpm.tw_connection_profile = connection_profile
				#cpm.source += " " connection_profile.source
				cpm.save()
				merge_fields(cpm, connection_profile)
		else: #no merged objects exists, so create ones
			print "could not merge - matches for ", smart_str(fn), ", ", smart_str(ln), " = ", matches_mp
			#create new merged profile for connection_profile
			if connection_profile.source == 'facebook':
				if len(mps.filter(fb_connection_profile=connection_profile)) == 0:
					cpm = Connection_Profile_Merged(user=user, fb_connection_profile=connection_profile)
				else:
					return
			if connection_profile.source == 'linkedin':
				if len(mps.filter(li_connection_profile=connection_profile)) == 0:
					cpm = Connection_Profile_Merged(user=user, li_connection_profile=connection_profile)
				else:
					return
			if connection_profile.source == 'twitter':
				if len(mps.filter(tw_connection_profile=connection_profile)) == 0:
					cpm = Connection_Profile_Merged(user=user, tw_connection_profile=connection_profile)
				else:
					return

			#set first and last name of new merged profile
			cpm.first_name = connection_profile.first_name
			cpm.last_name = connection_profile.last_name
			cpm.source = connection_profile.source
			cpm.locale = connection_profile.locale

			cpm.save()
			log_msg = "cpm saved: " + str(cpm)
			logger.info(log_msg)
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in merge_profile user, connection_profile") + str(e)
		print msg
		logger.error(msg)

#determines whether cp1 and cp2 are the same person
#cp1 and cp2 are both connection profile objects
#returns true if cp1 and cp2 are the same person
#Note: need to add more attribute checks later - not just first and last name
def match(cp1, cp2):
	fn1 = "none"
	ln1 = "none"
	fn2 = "none"
	ln2 = "none"

	if cp1 is None:
		print "****cp1 is none"
		return False
	else:
		fn1 = cp1.first_name
		ln1 = cp1.last_name

	if cp2 is None:
		return False
	else:
		fn2 = cp2.first_name
		ln2 = cp2.last_name

	fn_match = fn1.lower() in fn2.lower() or fn2.lower() in fn1.lower()
	ln_match = ln1.lower() in ln2.lower() or ln2.lower() in ln1.lower()

	if fn_match and ln_match: #only return True if both first names and last names of two connection profiles match
		return True
	else:
		return False

#def get_merged_profile(user, connection):
#	merged_profile = controller.get_merged_profile(connection)
#	print "get_merged_profile for ", user, "= ", merged_profile
#
#	#create a new merged profile object if none exist
#	if len(merged_profile) == 0:
#		if connection.source == 'facebook':
#			merged_profile = Connection_Profile_Merged(user=user, fb_connection_profile=connection)
#		if connection.source == 'linkedin':
#			merged_profile = Connection_Profile_Merged(user=user, li_connection_profile=connection)
#		if connection.source == 'twitter':
#			merged_profile = Connection_Profile_Merged(user=user, tw_connection_profile=connection)
#
#		#set first and last name of new merged profile
#		merged_profile.first_name = connection.first_name
#		merged_profile.last_name = connection.last_name
#		merged_profile.source = connection.source
#		merged_profile.locale = connection.locale
#
#		merged_profile.save()
#	else:
#		print "merged already exists for connection ", connection
#
#	return merged_profile

#integrates the fields of each of the connection profiles that are pointed to by this Connection_Profile_Merged
#parameter - a Connection_Profile_Merged object whose fields need to be combined
def merge_fields(cpm, cp):

	if cp.source =='facebook' and cp is not None:
		print "****MERGE FB FIELDS*****"
		merge_fields_fb(cpm, cp)
		cpm.save()

	if cp.source == 'linkedin' and cp is not None:
		print "****MERGE LI FIELDS*****"
		merge_fields_li(cpm, cp)
		cpm.save()

	if cp.source == 'twitter' and cp is not None:
		print "****MERGE TW FIELDS*****"
		merge_fields_tw(cpm, cp)
		cpm.save()

	return "not implemented"


def merge_fields_fb(cpm, cp):
	try:
		# Profile creation time and update time
		cpm.created_on_fb = cp.created_on
		cpm.last_saved_on_fb = cp.last_saved_on

		# Fields for source network information
		cpm.source_id_fb = cp.source_id
		#add connection source to merged profile if it doesn't already exist in source
		if "facebook" not in cpm.source:
			cpm.source += " facebook"

		cpm.userame_fb = cp.username
		cpm.first_name_fb = cp.first_name
		cpm.last_name_fb = cp.last_name
		cpm.name_fb = cp.name
		cpm.birthday_fb = cp.birthday
		cpm.picture_fb = cp.picture
		cpm.profile_url_fb = cp.profile_url
		cpm.website_fb = cp.website
		cpm.title_fb = cp.title
		#don't set locale, already when merged profile is created
		cpm.proxied_email_fb = cp.proxied_email

		#TODO: is_app_user??
		cpm.significant_other_id = cp.significant_other_id
		#TODO: are_friends???

		cpm.phone_numbers_fb = cp.phone_numbers
		cpm.degree_of_separation_fb = cp.degree_of_separation

		#TODO: when is emotional, physical, and total accessibility set??
	#
	# 	emotional_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	physical_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	total_accessibility = models.IntegerField(default=100, null=True, blank=True)

		cpm.specialities_fb = cp.specialties
		cpm.skills_fb = cp.skills
		cpm.num_connections_fb = cp.num_connections

		cpm.current_location_fb = cp.current_location
		cpm.hometown_location_fb = cp.hometown_location

		cpm.save()
		set_interests(cp, cpm)
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in merge_fields") + str(e)
		print msg
		logger.error(msg)


def merge_fields_li(cpm, cp):
	try:
		# Profile creation time and update time
		cpm.created_on_li = cp.created_on
		cpm.last_saved_on_li = cp.last_saved_on

		# Fields for source network information
		cpm.source_id_li = cp.source_id
		#add connection source to merged profile if it doesn't already exist in source
		if "linkedin" not in cpm.source:
			cpm.source += " linkedin"

		cpm.userame_li = cp.username
		cpm.first_name_li = cp.first_name
		cpm.last_name_li = cp.last_name
		cpm.name_li = cp.name
		cpm.birthday_li = cp.birthday
		cpm.picture_li = cp.picture
		cpm.profile_url_li = cp.profile_url
		cpm.website_li = cp.website
		cpm.title_li = cp.title
		#don't set locale, already when merged profile is created
		cpm.proxied_email_li = cp.proxied_email

		#TODO: is_app_user??
		#TODO: are_friends???

		cpm.phone_numbers_li = cp.phone_numbers
		cpm.degree_of_separation_li = cp.degree_of_separation

		#TODO: when is emotional, physical, and total accessibility set??
	#
	# 	emotional_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	physical_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	total_accessibility = models.IntegerField(default=100, null=True, blank=True)

		cpm.specialities_li = cp.specialties
		cpm.skills_li = cp.skills
		cpm.num_connections_li = cp.num_connections

		cpm.current_location_li = cp.current_location
		cpm.hometown_location_li = cp.hometown_location

		cpm.save()
		set_interests(cp, cpm)
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in merge_fields") + str(e)
		print msg
		logger.error(msg)

def merge_fields_tw(cpm, cp):
	try:
		# Profile creation time and update time
		cpm.created_on_tw = cp.created_on
		cpm.last_saved_on_tw = cp.last_saved_on

		# Fields for source network information
		cpm.source_id_tw = cp.source_id
		#add connection source to merged profile if it doesn't already exist in source
		if "twitter" not in cpm.source:
			cpm.source += " twitter"

		cpm.userame_tw = cp.username
		cpm.first_name_tw = cp.first_name
		cpm.last_name_tw = cp.last_name
		cpm.name_tw = cp.name
		cpm.birthday_tw = cp.birthday
		cpm.picture_tw = cp.picture
		cpm.profile_url_tw = cp.profile_url
		cpm.website_tw = cp.website
		cpm.title_tw = cp.title
		#don't set locale, already when merged profile is created
		cpm.proxied_email_tw = cp.proxied_email

		#TODO: is_app_user??
		cpm.significant_other_id = cp.significant_other_id
		#TODO: are_friends???

		cpm.phone_numbers_tw = cp.phone_numbers
		cpm.degree_of_separation_tw = cp.degree_of_separation

		cpm.twitter_accounts = cp.twitter_accounts
		#TODO: when is emotional, physical, and total accessibility set??
	#
	# 	emotional_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	physical_accessibility = models.IntegerField(default=50, null=True, blank=True)
	# 	total_accessibility = models.IntegerField(default=100, null=True, blank=True)

		cpm.specialities_tw = cp.specialties
		cpm.skills_tw = cp.skills
		cpm.num_connections_tw = cp.num_connections

		cpm.current_location_tw = cp.current_location
		cpm.hometown_location_tw = cp.hometown_location

		#set_interests(cp, cpm)
		#cpm.interests_tw = cp.interests
		cpm.save()
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in merge_fields") + str(e)
		print msg
		logger.error(msg)

#gets lists of all interests from cp and sets another pointer to the corresponding connection_profile_merged object
def set_interests(cp, cpm):
	try:
		interests = Connection_OtherInfo.objects.filter(conn_prof=cp)
		for i in interests:
			i.conn_prof_merged = cpm
			i.save()
	except Exception, e:
		msg = str(datetime.datetime.now()) + str("Exception in set_interests") + str(e)
		print msg
		logger.error(msg)

#match users - need to check this code, can only be run after all fb and linked in data
#currently only merges fb and li people, have not done twitter yet
def merge_contacts(user):
	linkedin_ppl = user.connection_profile_set.filter(source="linkedin")
	# print linkedin_ppl
	fb_data_exists = len(user.connection_profile_set.filter(source="facebook"))
	# print fb_data_exists
	# Run merge only if both linkedin_ppl and fb_ppl exist for that user
	if len(linkedin_ppl) and fb_data_exists:
		# print "Going into loop"
		for lp in linkedin_ppl:
			# li_id = lp.source_id
			li_first = lp.first_name
			li_last = lp.last_name
			# Check if two people with same name exist in LinkedIn. Don't merge in case two people with the same name exist as that is a bug on network.
			number_fb_ppl = len(user.connection_profile_set.filter(source='linkedin', first_name=li_first, last_name=li_last))
			# print 'number_fb_ppl:', number_fb_ppl
			if number_fb_ppl > 1:
				continue
			# Get potential facebook matches
			fb_ppl = user.connection_profile_set.filter(source="facebook", first_name__icontains=li_first, last_name__icontains=li_last)
			if len(fb_ppl) > 1 or len(fb_ppl) == 0:
				continue
			#len(fb_ppl) is 1
			fp = fb_ppl[0]
			fb_first = fp.first_name
			fb_last = fp.last_name
			# Boolean fields indicating is there a firstname match and lastname match
			firstname_match = li_first.lower() in fb_first.lower() or fb_first.lower() in li_first.lower()
			lastname_match = li_last.lower() in fb_last.lower() or fb_last.lower() in li_last.lower()

			#do we want to match other fields? Not yet.
			try:
				if (firstname_match and lastname_match):
					merged_exists = len(user.connection_profile_merged_set.filter(fb_connection_profile=fp, li_connection_profile=lp))
					if not merged_exists:
						#create new Connection_Profile_Merged
						#TODO: create a list of more than one fb contacts that have the same name. Do not merge in case there is more than one.
						cpm = Connection_Profile_Merged(user=user, fb_connection_profile=fp, li_connection_profile=lp)
						cpm.save()
						print cpm
					else:
						print "merge exists for ", fp, " and ", lp
				else:
					continue
			except Exception, e:
				print 'Exception:', Exception, e
				continue

# Function to get ProjectxUserProfile
def get_or_create_user_profile(request):
	profile = None
	user = request.user
	try:
		profile = user.get_profile()
	except SBUserProfile.DoesNotExist:
		profile = SBUserProfile.objects.create(user=request.user)
	return profile

def merge_on_demand(request):
	try:
		merge(request.user, "facebook")
		merge(request.user, "linkedin")
		merge(request.user, "twitter")
		return HttpResponse("Your social connections have been merged! <a href='/"+settings.APP_URL+"'> Home<a>")
	except Exception, e:
		msg = str(datetime.datetime.now()) + str(Exception) + str(e)
		print msg
		logger.error(msg)
