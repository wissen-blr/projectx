from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver

import datetime

import sys
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("projectx")

#TODO change class names to camel case naming convention

# All Model or Class names need to be in CamelCase, i.e. like ClassName rather than with underscores

# Class used to store Interests (FB), Likes (FB), Skills (LI)


class SBUserProfile(models.Model):
	user = models.OneToOneField(User)

	#Other fields here
	notes_field = models.CharField(max_length=200, blank=True)
	source = models.CharField(max_length=200, blank=True)
	source_id = models.CharField(max_length=200, blank=True)
	first_name = models.CharField(max_length=200, blank=True)
	last_name = models.CharField(max_length=200, blank=True)

	# ManyToMany relationship, One connection can have many interests, One interest can be associated with multiple users
#	interests = models.ManyToManyField(Connection_OtherInfo, blank=True)

	# education_info and work_info stored in Education_Info and Work_Info models

#	@receiver(post_save, sender=User)
#	def create_profile(sender, instance, created, **kwargs):
#	#Create a matching profile whenever a user object is created.
#		if created:
#			profile, new = SBUserProfile.objects.get_or_create(user=instance)

	def __unicode__(self):
		return self.user.username

class Location(models.Model):
	#TODO duplicate locations being created when saving facebook data. Save function should check if location exists, and allocate it to that location. See save_linkedin_connection_profile()
	# Complete location name e.g. Cambridge, Massachusetts or Boston, MA, whatever is coming from source network
	name = models.CharField(max_length=200, blank=True)

	street = models.CharField(max_length=200, blank=True)
	city = models.CharField(max_length=50, blank=True)
	state = models.CharField(max_length=50, blank=True)
	country = models.CharField(max_length=50, blank=True)

	zip  = models.BigIntegerField(null=True,blank=True)
	latitude  = models.FloatField(null=True,blank=True)
	longitude = models.FloatField(null=True,blank=True)

	def __unicode__(self):
		return u'%s' % (self.name)

# Class used to store all connection information
class Connection_Profile(models.Model):
	# Link to user logging into system
	user = models.ForeignKey(User)

	# Profile creation time and update time
	created_on = models.DateTimeField(auto_now_add=True, default=datetime.datetime.today())
	last_saved_on = models.DateTimeField(auto_now=True, default=datetime.datetime.today())

	# Fields for source network information
	source_id = models.CharField(max_length=100)
	source = models.CharField(max_length=200, blank=True)
	username = models.CharField(null=True, max_length=200, blank=True)
	first_name = models.CharField(max_length=200, blank=True)
	last_name = models.CharField(max_length=200, blank=True)
	name = models.CharField(max_length=200, blank=True) # User's full name from Twitter usually
	birthday = models.DateField(null=True, blank=True)
	picture  = models.URLField(null=True,blank=True)
	profile_url  = models.URLField(null=True,blank=True)
	website  = models.URLField(null=True, blank=True)
	title = models.CharField(null=True,max_length=200, blank=True)
	locale = models.CharField(null=True,max_length=200, blank=True) # e.g. 'en_US', not to be confused with location
	proxied_email = models.CharField(null=True,max_length=200, blank=True)
	is_app_user = models.CharField(max_length=200, blank=True)
	significant_other_id = models.CharField(max_length=200, blank=True)
	are_friends = models.BooleanField(blank=True)

#	books = models.CharField(max_length=200, blank=True)
#	movies = models.CharField(max_length=200, blank=True)
#	music = models.CharField(max_length=200, blank=True)

	phone_numbers = models.CharField(max_length=200, blank=True)
	degree_of_separation = models.IntegerField(blank=True) # Degree of separation from SB user

	emotional_accessibility = models.IntegerField(default=50, null=True, blank=True)
	physical_accessibility = models.IntegerField(default=50, null=True, blank=True)
	total_accessibility = models.IntegerField(default=100, null=True, blank=True)

	twitter_accounts = models.CharField(max_length=200, blank=True)
	specialties = models.CharField(max_length=200, blank=True)
	skills = models.CharField(max_length=400, blank=True)
	#TODO Duplicated info, industry also stored in work_info object
#	industries = models.CharField(max_length=200, blank=True)
	num_connections = models.IntegerField(null=True, blank=True)

	# ManyToOne relationship Multiple connections can have same Location
	current_location = models.ForeignKey(Location, null=True, related_name="current_loc")
	hometown_location = models.ForeignKey(Location, null=True, related_name="hometown_loc")

	# ManyToMany relationship, One connection can have many interests, One interest can be associated with multiple users
	#interests = models.ForeignKey(Connection_OtherInfo, null=True, related_name="interests")

	# LinkedIn search has text field interests, but it contains plain text.
	interests_li = models.CharField(max_length=400, blank=True)

	# Educations can be accessed from Education_Info model
	#education_history = models.OneToOneField(Education_Info)
	#current_work_info = models.ManyToManyField(Work_Info)
	#past_work_info = models.ManyToManyField(Work_Info)
	#events = models.ManyToManyField(Event)

	def __unicode__(self):
		return u'%s %s id:%s %s' % (self.first_name, self.last_name, self.id, self.source)

	def save_facebook_connection_profile(self, json_data, src, from_id):
		self.source_id = nvl(json_data, "id")
		self.source = src
		self.username =  nvl(json_data, "username")
		self.first_name  = nvl(json_data, "first_name")
		self.last_name = nvl(json_data,"last_name")
#		# Save birthday
#		if nvl(json_data, "birthday"):
#			birth_month = int(nvl(json_data, "birthday")[0:2])
#			birth_day = int(nvl(json_data, "birthday")[3:5])
#			if len(nvl(json_data, "birthday"))>5:
#				birth_year = int(nvl(json_data, "birthday")[6:])
#			else:
#				birth_year = 1900
#			self.birthday = datetime.date(birth_year, birth_month, birth_day)
#		else:
#			self.birthday = datetime.date(1900, 01, 01)
		self.picture  = nvl(json_data,"picture")
		self.profile_url  = "http://www.facebook.com/"+nvl(json_data, "id")
		self.website  = nvl(json_data,"website")
		#self.title = ""
#		self.locale = nvl(json_data,"locale")
		#self.proxied_email = nvl(json_data,"email")
		#self.is_app_user = ""
		#self.significant_other_id = nvl(json_data["significant_other"]["id"])
		#self.are_friends = ""

		#self.phone_numbers = ""
		#self.num_connections = ""
		#self.twitter_accounts = ""
		#self.specialties = nvl(json_data["specialties"])
		#self.skills = nvl(json_data["skills"])
		#self.industries = nvl(json_data["industries"])

		#self.books =
		#self.interests = models.CharField(max_length=200, blank=True)
		#self.movies = models.CharField(max_length=200, blank=True)
		#self.music = models.CharField(max_length=200, blank=True)

		if nvl(json_data, "location"):
			location = Location.objects.create()
			location.name = nvl(json_data["location"], "name")
			#TODO parse location info into columns
			location.street = ""
			location.city = ""
			location.state = ""
			#location.country = ""
			#location.zip  = 1
			#location.latitude  = 1
			#location.longitude = 1
			location.save()
			self.current_location = location

		if nvl(json_data, "hometown"):
			location = Location.objects.create()
			location.name = nvl(json_data["hometown"], "name")
			location.street = ""
			location.city = ""
			location.state = ""
			#location.country = ""
			#location.zip  = 1
			#location.latitude  = 1
			#location.longitude = 1
			location.save()
			self.hometown = location

		# Save Connection_Profile as id is required in for storing educations
		self.save()

		# Get interests from facebook data
#		if nvl(json_data, "interests"):
#			for interest in nvl(json_data["interests"], "data"):
#				name = nvl(interest, "name")
#				category = nvl(interest, "category")
#				info_type = "interest"
#				new_interest = Connection_OtherInfo(name=name, category=category, info_type=info_type)
#				new_interest.save()
#				new_interest.connection_profile_set.add(self)

		# Get likes from facebook data
		if nvl(json_data, "likes"):
			for like in nvl(json_data["likes"], "data"):
				conn_prof = self
				name = nvl(like, "name")
				category = nvl(like, "category")
				info_type = "like"
				facebook_id = nvl(like, "id")
				#check if like exists for this user
				like_exists = Connection_OtherInfo.objects.filter(conn_prof=conn_prof, name=name, category=category, info_type=info_type, facebook_id=facebook_id)
				if not len(like_exists):
					try:
						new_like = Connection_OtherInfo(conn_prof=conn_prof, name=name, category=category, info_type=info_type, facebook_id=facebook_id)
						new_like.save()
						#new_like.connection_profile_set.add(self) 
					except Exception,e:
						print Exception, e
						logger.error(e)
				else:
					try:
						like = like_exists[0]
						like.connection_profile_set.add(self)
					except Exception,e:
						print Exception, e
						logger.error(e)
		else:
			#Store a dummy like if no likes exist, otherwise connection_profile doesn't show up in search results with blank interest filter
			new_like = Connection_OtherInfo(conn_prof=self, name='', category='', info_type='like')
			new_like.save()

		#if "events" in json_data
		if nvl(json_data, "events"):
			if len(json_data["events"]["data"]) > 0:
				for event_record in json_data["events"]["data"]:
					event = Event.objects.create(connection_profile=self)
					#event.connection_profile = self
					event.name  = nvl(event_record,"name")
					event.source_id = nvl(event_record, "id")
					event.location = nvl(event_record,"location")
					event.rsvp_status = nvl(event_record,"rsvp_status")
					#event.start_time = nvl(event_record,"start_time")
					#event.end_time = nvl(event_record,"end_time")
					#self.events.add(event)
					event.save()
					#print "Event ID", event

		if nvl(json_data, "education"):
			for education_record in json_data["education"]:
				name1 = nvl(education_record["school"], "name")
				year1 = None
				if nvl(education_record, "year"):
					try:
						year1  = nvl(education_record["year"], "name")
					except ValueError:
						print "ValueError in parsing " + education_record["year"]

				concentration1  = "" #education_record["concentration"]["name"]
				degree1  = "" #education_record["degree"]["name"]
				school_type1  = "" #education_record["school_type"]
				#Check if education exists for this user
				edu_exists = Education_Info.objects.filter(connection_profile=self, name=name1, year=year1)
				if not len(edu_exists):
					try:
						education_info = Education_Info.objects.create(connection_profile=self, name=name1, year=year1, concentration=concentration1, degree=degree1, school_type=school_type1)
						education_info.save()
					except Exception, e:
						print "Unable to save Education Info for"
						print education_record
						print e

		if nvl(json_data, "work"):
			for work_record in json_data["work"]:
				work = Work_Info.objects.create(connection_profile=self)
				#work.connection_profile = self
				name = ''
				if nvl(work_record,"employer"):
					name = nvl(work_record["employer"],"name")
					work.company_name  = name
				title = ''
				if nvl(work_record,"position"):
					title = nvl(work_record["position"], "name")
					work.position = title
				work.description  = nvl(work_record,"description")
				if nvl(work_record,"location"):
					work.location = nvl(work_record["location"], "name")
				#work.start_date = nvl(work_record,"start_date")
				#work.end_date = nvl(work_record,"end_date")
				#Check if job exists for this user
				job_exists = Work_Info.objects.filter(connection_profile=self, company_name=name, position=title)
				if not len(job_exists):
					try:
						work.save()
					except Exception, e:
						msg = str(datetime.datetime.now()) + str(Exception) + " " + str(e)
						print msg
						logger.error(msg)

		#Save groups if present from facebook
		if nvl(json_data, "groups"):
			for group in nvl(json_data["groups"], "data"):
				name = nvl(group, "name")
				source = "facebook"
				source_id = nvl(group, "id")
				url = "http://www.facebook.com/"+nvl(group, "id")
				try:
					#Check if group exists for this user
					group_exists = Group.objects.filter(connection_profile=self, source_id=source_id)
					if not len(group_exists):
						group = Group.objects.create(connection_profile=self, name=name, source=source, source_id=source_id, url=url)
						group.save()
				except Exception, e:
					print "Unable to save group info:", name, source_id
					print e

#		#Creating links for social graph representation.
#		link = Link.objects.create()
#		link.SB_UserID_from = self.user.id
#		link.SB_UserID_to = self.user.id
#		link.Source = src
#		link.Id_from = from_id
#		link.Id_to = self.source_id
#		link.Dos = 1
#		link.isSymmetricLink = True
#		link.strength = 1
#		link.save()
#
#		link2 = Link.objects.create()
#		link2.SB_UserID_from = self.user.id
#		link2.SB_UserID_to = self.user.id
#		link2.Source = src
#		link2.Id_from = self.source_id
#		link2.Id_to = from_id
#		link2.Dos = 1
#		link2.isSymmetricLink = True
#		link2.strength = 1
#		link2.save()

	def save_linkedin_connection_profile(self, json_data):
		self.source_id = nvl(json_data, "id")
		self.source = "linkedin"
		self.first_name  = nvl(json_data, "firstName")
		self.last_name = nvl(json_data, "lastName")
		self.picture  = nvl(json_data, "pictureUrl")
		self.profile_url  = nvl(json_data, "publicProfileUrl")
		self.title = nvl(json_data, "headline")
#		self.locale = "" #Not available from linkedIn
		self.num_connections = nvl(json_data, "numConnections")

		self.phone_numbers = ""
		if nvl(json_data, "phoneNumbers"):
			if nvl(json_data["phoneNumbers"], "_total"):
				if nvl(json_data["phoneNumbers"], "_total") > 0:
	#				num_phones = nvl(json_data["phoneNumbers"], "_total")
					self.phone_numbers = nvl(json_data["phoneNumbers"]["values"][0], "phoneNumber")

		self.skills = ""
		if nvl(json_data, "skills"):
			if nvl(json_data["skills"], "_total") > 0:
#				num_skills = nvl(json_data["skills"], "_total")
				skills_list = []
				for skill in nvl(json_data["skills"],"values"):
					skills_list.append(nvl(skill["skill"],"name"))
					skills_list.append(",")
				self.skills = ''.join(skills_list)

		# Save Connection_Profile as id is required in for storing educations
		self.save()

		# Store current_location
		if nvl(json_data, "location"):
			location_name = nvl(json_data["location"], "name")
			#Check if location exists
			l_exists_list = Location.objects.filter(name=location_name)
			if len(l_exists_list):
				location = l_exists_list[0]
				self.current_location = location
			else:
				location = Location.objects.create()
				location.name=location_name
				location.save()
				self.current_location = location

		# store interests from interests text field
		if nvl(json_data, "interests"):
			self.interests_li = nvl(json_data, "interests")
			# Storing this data into interests model is giving very bad results.
			# int_list = []
			# for interest in interests.split(','):
				# int_list.append(interest.strip())
			# for interest in int_list:
				# name = interest
				# category = ""
				# info_type = "interest"
				# new_interest = Connection_OtherInfo(name=name, category=category, info_type=info_type)
				# new_interest.save()
				# new_interest.connection_profile_set.add(self)

		# store educations
		if nvl(json_data, "educations"):
			if nvl(json_data["educations"], "_total")>0:
				for education_record in json_data["educations"]["values"]:
					name = nvl(education_record, "schoolName")
					# Get end year
					year = None
					if nvl(education_record, "endDate"):
						if nvl(education_record["endDate"],"year"):
							year = nvl(education_record["endDate"],"year")
					# Get concentration (fieldOfStudy)
					concentration = ""
					if nvl(education_record, "fieldOfStudy"):
						concentration = nvl(education_record, "fieldOfStudy")
					# Get degree
					degree = ""
					if nvl(education_record, "degree"):
						degree = nvl(education_record, "degree")
					#Check if education exists for this user
					edu_exists = Education_Info.objects.filter(connection_profile=self, name=name, year=year, concentration=concentration, degree=degree)
					if not len(edu_exists):
						# Create Education_Info object and save
						try:
							education_info = Education_Info(connection_profile=self, name=name, year=year, concentration=concentration, degree=degree)
							education_info.save()
						except Exception, e:
							print "Unable to save Education Info:", sys.exc_info()

		# store positions
		if nvl(json_data, "positions"):
			if nvl(json_data["positions"], "_total")>0:
				for work_record in json_data["positions"]["values"]:
					# Get company name
					name = nvl(work_record["company"], "name")
					# Get industry
					industry = nvl(work_record["company"], "industry")
					# Get position title, description
					title = nvl(work_record, "title")
					description = nvl(work_record, "summary")
					# Get start date
					start_date = None
					if nvl(work_record, "startDate"):
						if nvl(work_record["startDate"], "year"):
							start_year = nvl(work_record["startDate"], "year")
						else:
							start_year = 1900
						if nvl(work_record["startDate"], "month"):
							start_month = nvl(work_record["startDate"], "month")
						else:
							start_month = 01
						start_date = datetime.date(start_year, start_month, 01)
					# Get end date
					if nvl(work_record, "isCurrent"):
						end_date = None
					elif nvl(work_record, "endDate"):
						if nvl(work_record["endDate"], "month"):
							end_month = nvl(work_record["endDate"], "month")
						else:
							end_month = 01
						if nvl(work_record["endDate"], "year"):
							end_year = nvl(work_record["endDate"], "year")
						else:
							end_year = 1900
						end_date = datetime.date(end_year, end_month, 01)
					else:
						end_date = None
					# Get isCurrent position
					if nvl(work_record, "isCurrent"):
						isCurrent = nvl(work_record, "isCurrent")
					else:
						isCurrent = False
					#Check if job exists for this user
					job_exists = Work_Info.objects.filter(connection_profile=self, company_name=name, position=title, description=description, industry=industry, start_date=start_date, end_date=end_date, isCurrent=isCurrent)
					if not len(job_exists):
						# Create work_info object and save
						try:
							work_info = Work_Info(connection_profile=self, company_name=name, position=title, description=description, industry=industry, start_date=start_date, end_date=end_date, isCurrent=isCurrent)
							work_info.save()
						except:
							print "Unable to save work info:", sys.exc_info()

		#Store a dummy like, otherwise connection_profile doesn't show up in search results with blank filter
		try:
			new_like = Connection_OtherInfo(conn_prof=self, name='', category='', info_type='like')
			new_like.save()
		except Exception, e:
			msg = datetime.datetime.now() + str(Exception) + str(e)
			print msg
			logger.error(msg)
	def save_twitter_profile(self, json_data, src, type, my_id):
#		print src
		#name = json_data["name"]
		self.source_id = nvl(json_data, "id")
		self.source = src
		self.num_connections = nvl(json_data, "followers_count")
		self.profile_url = nvl(json_data,"profile_image_url_https")

		self.username =  nvl(json_data, "name")
		name = nvl(json_data, "name")
		parsed_name = parse_name(name)
		self.first_name =  parsed_name["FirstName"]
		self.last_name =  parsed_name["LastName"]

		self.locale = nvl(json_data,"lang")
		self.website  = nvl(json_data,"url")


		if nvl(json_data, "status"):
			if nvl(json_data["status"], "place"):
				location = Location.objects.create()
				location.name = nvl(json_data["status"]["place"], "full_name")
				location.street = ""
				location.city = nvl(json_data["status"]["place"], "name")
				location.state = "MA"
				location.country = nvl(json_data["status"]["place"], "country")
				#location.zip  = 1
				#location.latitude  = 1
				#location.longitude = 1
				location.save()
				self.current_location = location

		self.save()

		#Store a dummy like, otherwise connection_profile doesn't show up in search results with blank filter
		try:
			new_like = Connection_OtherInfo(conn_prof=self, name='', category='', info_type='like')
			new_like.save()
		except Exception, e:
			msg = datetime.datetime.now() + str(Exception) + str(e)
			print msg
			logger.error(msg)

		print "ID of newly saved connection" + str(self.id)

#		link = Link.objects.create()
#		link.SB_UserID_from = self.user.id
#		link.SB_UserID_to = self.user.id
#		link.Source = src
#		link.Id_from = self.source_id
#		link.Id_to = my_id
#		link.Dos = 1
#		if (type == "friends"):
#			link.isSymmetricLink = True
#		else:
#			link.isSymmetricLink = False
#		link.strength = 1
#		link.save()
#
#		if (type == "friends"):
#			link2 = Link.objects.create()
#			link2.SB_UserID_from = self.user.id
#			link2.SB_UserID_to = self.user.id
#			link2.Source = src
#			link2.Id_from = my_id
#			link2.Id_to = self.source_id
#			link2.Dos = 1
#			link2.isSymmetricLink = True
#			link2.strength = 1
#			link2.save()

#		self.save()

#fzhang - class used to store pointers to user information stored in different
#sources (fb, li, tw)
class Connection_Profile_Merged(models.Model):
	# Link to user logging into system
	user = models.ForeignKey(User)

	fb_connection_profile = models.OneToOneField(Connection_Profile, null=True, related_name="fb_connnection_profile")
	li_connection_profile = models.OneToOneField(Connection_Profile, null=True, related_name="li_connnection_profile")
	tw_connection_profile = models.OneToOneField(Connection_Profile, null=True, related_name="tw_connnection_profile")

	# Profile creation time and update time
	created_on_fb = models.DateTimeField(auto_now_add=True, default=datetime.datetime.today())
	created_on_li = models.DateTimeField(auto_now_add=True, default=datetime.datetime.today())
	created_on_tw = models.DateTimeField(auto_now_add=True, default=datetime.datetime.today())

	last_saved_on_fb = models.DateTimeField(auto_now=True, default=datetime.datetime.today())
	last_saved_on_li = models.DateTimeField(auto_now=True, default=datetime.datetime.today())
	last_saved_on_tw = models.DateTimeField(auto_now=True, default=datetime.datetime.today())

	# Fields for source network information
	source_id_fb = models.CharField(max_length=100, null=True)
	source_id_li = models.CharField(max_length=100, null=True)
	source_id_tw = models.CharField(max_length=100, null=True)

	source = models.CharField(max_length=200, blank=True)

	username_fb = models.CharField(null=True, max_length=200, blank=True)
	username_li = models.CharField(null=True, max_length=200, blank=True)
	username_tw = models.CharField(null=True, max_length=200, blank=True)

	first_name = models.CharField(max_length=200, blank=True)
	last_name = models.CharField(max_length=200, blank=True)

	name = models.CharField(max_length=200, blank=True) # User's full name from Twitter usually

	birthday = models.DateField(null=True, blank=True)

	picture_fb  = models.URLField(null=True,blank=True)
	picture_li  = models.URLField(null=True,blank=True)
	picture_tw = models.URLField(null=True,blank=True)

	profile_url_fb  = models.URLField(null=True,blank=True)
	profile_url_li  = models.URLField(null=True,blank=True)
	profile_url_tw  = models.URLField(null=True,blank=True)

	website_fb  = models.URLField(null=True, blank=True)
	website_li  = models.URLField(null=True, blank=True)
	website_tw  = models.URLField(null=True, blank=True)

	title_fb = models.CharField(null=True,max_length=200, blank=True)
	title_li = models.CharField(null=True,max_length=200, blank=True)
	title_tw = models.CharField(null=True,max_length=200, blank=True)

	locale = models.CharField(null=True,max_length=200, blank=True) # e.g. 'en_US', not to be confused with location

	proxied_email_fb = models.CharField(null=True,max_length=200, blank=True)
	proxied_email_li = models.CharField(null=True,max_length=200, blank=True)
	proxied_email_tw = models.CharField(null=True,max_length=200, blank=True)

	is_app_user = models.CharField(max_length=200, blank=True)
	significant_other_id = models.CharField(max_length=200, blank=True)
	are_friends = models.BooleanField(blank=True)

#	books = models.CharField(max_length=200, blank=True)
#	movies = models.CharField(max_length=200, blank=True)
#	music = models.CharField(max_length=200, blank=True)

	phone_numbers_fb = models.CharField(max_length=200, blank=True)
	phone_numbers_li = models.CharField(max_length=200, blank=True)
	phone_numbers_tw = models.CharField(max_length=200, blank=True)

	degree_of_separation_fb = models.IntegerField(blank=True, null=True) # Degree of separation from SB user
	degree_of_separation_li = models.IntegerField(blank=True, null=True) # Degree of separation from SB user
	degree_of_separation_tw = models.IntegerField(blank=True, null=True) # Degree of separation from SB user

	emotional_accessibility = models.IntegerField(default=50, null=True, blank=True)
	physical_accessibility = models.IntegerField(default=50, null=True, blank=True)
	total_accessibility = models.IntegerField(default=100, null=True, blank=True)

	twitter_accounts = models.CharField(max_length=200, blank=True)

	specialties_fb = models.CharField(max_length=200, blank=True)
	specialties_tw = models.CharField(max_length=200, blank=True)
	specialties_li = models.CharField(max_length=200, blank=True)

	skills_fb = models.CharField(max_length=400, blank=True)
	skills_tw = models.CharField(max_length=400, blank=True)
	skills_li = models.CharField(max_length=400, blank=True)

	#TODO Duplicated info, industry also stored in work_info object
#	industries = models.CharField(max_length=200, blank=True)
	num_connections_fb = models.IntegerField(null=True, blank=True)
	num_connections_li = models.IntegerField(null=True, blank=True)
	num_connections_tw = models.IntegerField(null=True, blank=True)

	# ManyToOne relationship Multiple connections can have same Location
	current_location_fb = models.ForeignKey(Location, null=True, related_name="current_loc_fb")
	current_location_li = models.ForeignKey(Location, null=True, related_name="current_loc_li")
	current_location_tw= models.ForeignKey(Location, null=True, related_name="current_loc_tw")

	hometown_location_fb = models.ForeignKey(Location, null=True, related_name="hometown_loc_fb")
	hometown_location_li= models.ForeignKey(Location, null=True, related_name="hometown_loc_li")
	hometown_location_tw = models.ForeignKey(Location, null=True, related_name="hometown_loc_tw")

	# ManyToMany relationship, One connection can have many interests, One interest can be associated with multiple users
	#interests_fb = models.ManyToManyField(Connection_OtherInfo, blank=True)
	#interests_li= models.CharField(max_length=400, blank=True)
	#interests_tw = models.CharField(max_length=400, blank=True)

	# LinkedIn search has text field interests, but it contains plain text.
	#interests_li = models.CharField(max_length=400, blank=True)

	# Educations can be accessed from Education_Info model
	#education_history = models.OneToOneField(Education_Info)
	#current_work_info = models.ManyToManyField(Work_Info)
	#past_work_info = models.ManyToManyField(Work_Info)
	#events = models.ManyToManyField(Event)

	def __unicode__(self):
		return u'%s %s %s' % (self.fb_connection_profile, self.li_connection_profile, self.tw_connection_profile)


#*****not sure how to write unicode function for this!

#fzhang - class used to stored information about each merged SB user
# should hold aggregate information about users across different sources and
# variant connection profiles of the same user
# so far, all fields copied from ConnectionProfile
# class SB_Person_Merged(models.Model):
# 	# Link to user logging into system
# 	user = models.ForeignKey(User)
#
# 	# Fields for source network information
# 	source_id = models.CharField(max_length=100)
# 	name = models.CharField(max_length=200, blank=True)
# 	source = models.CharField(max_length=200, blank=True)
# 	username = models.CharField(null=True, max_length=200, blank=True)
# 	first_name = models.CharField(max_length=200, blank=True)
# 	last_name = models.CharField(max_length=200, blank=True)
# 	birthday = models.DateField(null=True, blank=True)
# 	picture  = models.URLField(null=True,blank=True)
# 	profile_url  = models.URLField(null=True,blank=True)
# 	website  = models.URLField(null=True, blank=True)
# 	title = models.CharField(null=True,max_length=200, blank=True)
# 	locale = models.CharField(null=True,max_length=200, blank=True) # e.g. 'en_US', not to be confused with location
# 	proxied_email = models.CharField(null=True,max_length=200, blank=True)
# 	is_app_user = models.CharField(max_length=200, blank=True)
# 	significant_other_id = models.CharField(max_length=200, blank=True)
# 	are_friends = models.BooleanField(blank=True)
#
# 	books = models.CharField(max_length=200, blank=True)
# 	movies = models.CharField(max_length=200, blank=True)
# 	music = models.CharField(max_length=200, blank=True)
#
# 	phone_numbers = models.CharField(max_length=200, blank=True)
# 	degree_of_separation = models.IntegerField(blank=True) # Degree of separation from SB user
# 	twitter_accounts = models.CharField(max_length=200, blank=True)
# 	specialties = models.CharField(max_length=200, blank=True)
# 	skills = models.CharField(max_length=400, blank=True)
# 	#TODO Duplicated info, industry also stored in work_info object
# 	industries = models.CharField(max_length=200, blank=True)
# 	num_connections = models.IntegerField(null=True, blank=True)
#
# 	#fzhang OneToOne relationship - one connection has one copy of a friend connection profile
# 	#should be OneToMany but can't find the field in django
# 	connection_profile_merged_key = models.ManyToManyField(Connection_Profile_Merged, null=True, related_name="connection_pf_merged_key")
# 	#do i also need a key that ties this connectionProfileMerged instance back to
# 	# a SBUserMerged?
#
# 	# ManyToOne relationship Multiple connections can have same Location
# 	current_location = models.ForeignKey(Location, null=True, related_name="current_loc")
# 	hometown_location = models.ForeignKey(Location, null=True, related_name="hometown_loc")
#
# 	# ManyToMany relationship, One connection can have many interests, One interest can be associated with multiple users
# 	interests = models.ManyToManyField(Connection_OtherInfo, blank=True)
#
# 	def __unicode__(self):
# 		return u'%s %s id:%s %s' % (self.first_name, self.last_name, self.id, self.source)

class Connection_OtherInfo(models.Model):
	conn_prof = models.ForeignKey(Connection_Profile, blank=True, null=True)
	conn_prof_merged = models.ForeignKey(Connection_Profile_Merged, blank=True, null=True)
	name = models.CharField(max_length=200, blank=True) #Cannot be blank
	category = models.CharField(max_length=200, blank=True) #Category from source
	info_type = models.CharField(max_length=200) #Indicates whether info is interest, like, skill
	facebook_id = models.CharField(max_length=200, blank=True) #For likes, also store the facebook id to take user to page
	def __unicode__(self):
		return u'%s, %s <- %s' % (self.name, self.category, self.info_type)
def nvl(data, field):
	try:
		return data[field]
	except ValueError:
		return None
	except:
		return None

class Education_Info(models.Model):
	connection_profile = models.ForeignKey(Connection_Profile)
	name  = models.CharField(max_length=200, blank=True)
	year  = models.IntegerField(null=True,blank=True)
	concentration  = models.CharField(max_length=200, blank=True)
	degree  = models.CharField(max_length=200, blank=True)
	school_type  = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return u'%s->%s ' % (self.name, self.year)

class Work_Info(models.Model):
	connection_profile = models.ForeignKey(Connection_Profile)
	location = models.CharField(max_length=200, blank=True) #TODO Location type. We might need to remove this, not using it
	company_name = models.CharField(max_length=200, blank=True)
	position = models.CharField(null=True,max_length=200, blank=True)
	# Position description or summary
	description = models.CharField(null=True,max_length=200, blank=True)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	industry = models.CharField(max_length=200, blank=True)
	isCurrent = models.BooleanField()

	def __unicode__(self):
		return u'%s->%s ' % (self.company_name, self.position)

class Event(models.Model):
	connection_profile = models.ForeignKey(Connection_Profile)

	source_id = models.CharField(max_length=100, blank=True)
	name = models.CharField(max_length=200, blank=True)
	tagline = models.CharField(max_length=200, blank=True)
	pic = models.CharField(max_length=200, blank=True)
	host = models.CharField(max_length=200, blank=True)
	description = models.TextField(max_length=2000, blank=True)
	event_type = models.CharField(max_length=200, blank=True)
	event_subtype = models.CharField(max_length=200, blank=True)
	start_time = models.DateTimeField(null=True,blank=True)
	end_time = models.DateTimeField(null=True,blank=True)
	#location = models.OneToOneField(Location)
	venue = models.CharField(max_length=200, blank=True)
	rsvp_status  = models.CharField(max_length=200, blank=True)

	def __unicode__(self):
		return u'%s->%s ' % (self.name, self.rsvp_status)

class Group(models.Model):
	#ManyToMany relationship between Group and Connection_Profile
	connection_profile = models.ForeignKey(Connection_Profile)

	name = models.CharField(max_length=200, blank=True)
	source = models.CharField(max_length=200, blank=True)
	source_id = models.CharField(max_length=100, blank=True)
	url = models.URLField(null=True, blank=True)

	def __unicode__(self):
		return u'%s' % (self.name)

#This class has many to many relationship with Connection_Profile objects

class Link(models.Model):
	id = models.AutoField(primary_key=True)
	SB_UserID_from = models.CharField(max_length=200, blank=True)
	SB_UserID_to = models.CharField(max_length=200, blank=True)
	Source = models.CharField(max_length=200, blank=True)
	Id_from = models.CharField(max_length=200, blank=True)
	Id_to = models.TextField(max_length=2000, blank=True)
	Dos = models.IntegerField(null=True)
	isSymmetricLink = models.BooleanField(max_length=200, blank=True)
	strength = models.IntegerField(null=True)

	def __unicode__(self):
		return u'%s->%s ' % (self.Id_from, self.Id_to)


#Todo Retrieve all facebook user info from table like relationships, family info, see Akash's slide.
# Add social_links table and store them - Think this is DONE.

#Buckets for the recommendation engine
class RecommendationBucket(models.Model):
	#Each Recommendation Bucket is connected to a Merged Connection Profile
	merged_profile = models.OneToOneField(Connection_Profile)

	#The following columns will hold concatenated text of attributes for each profile
	locations = models.CharField(max_length=400, blank=True)
	educations = models.CharField(max_length=400, blank=True)
	industries = models.CharField(max_length=400, blank=True)
	skills = models.CharField(max_length=400, blank=True)
	music = models.CharField(max_length=400, blank=True)
	musician_bands = models.CharField(max_length=400, blank=True)
	book_genres = models.CharField(max_length=400, blank=True)
	movies = models.CharField(max_length=400, blank=True) #come from FB interests and likes
	television = models.CharField(max_length=400, blank=True)
	games = models.CharField(max_length=400, blank=True)
	sports_teams = models.CharField(max_length=400, blank=True)
	fav_sports = models.CharField(max_length=400, blank=True)
	field_of_studies = models.CharField(max_length=400, blank=True)

	def __unicode__(self):
		return u'id:%s %s' % (self.id, self.merged_profile)

class SearchConnectionRating(models.Model):
	#Each rating is related to the current SBUser
	user = models.ForeignKey(User)

	search_parameters = models.CharField(max_length=400) #Search parameters can't be blank/null
	connection_profile = models.ForeignKey(Connection_Profile, null=True)
	connection_profile_rank = models.IntegerField(null=True)
	rating = models.IntegerField()
	rating_comment = models.TextField(blank=True)
	notes = models.TextField(blank=True) #Doing this to test south migrations

	def __unicode__(self):
		return u'%s conn_id:%s rating:%s' % (self.search_parameters, self.connection_profile.id, self.rating)


class Twitter_Feed(models.Model):
	user_id = models.BigIntegerField(null=False,blank=True)
	source_id = models.CharField(max_length=200, blank=True)
	feed_id = models.CharField(max_length=200, blank=True)
	created_at = models.CharField(max_length=50, blank=True)
	text = models.CharField(max_length=300, blank=True)
	source = models.CharField(max_length=50, blank=True)

	place = models.CharField(max_length=200, null=True,blank=True)
	retweet_count = models.BigIntegerField(null=True,blank=True)
	favorited  = models.BooleanField(blank=True)
	retweeted = models.BooleanField(blank=True)

	def __unicode__(self):
		return u'%s' % (self.name)
	
	def save_twitter_feed(self, json_data, user_id, twitter_id):
		self.user_id = user_id
		self.source_id = twitter_id
		self.feed_id = nvl(json_data, "id")
		self.created_at = nvl(json_data, "created_at")
		self.text = nvl(json_data, "text")
		#self.source = nvl(json_data, "source") #TODO - does not work on Linux
		#json_data, "geo")
		#json_data, "coordinates")
		self.place = nvl(json_data, "place")
		self.retweet_count = nvl(json_data, "retweet_count")
		self.favorited = nvl(json_data, "favorited")
		self.retweeted = nvl(json_data, "retweeted")
	

def parse_name(name):
	fl = name.split()
	first_name = fl[0]
	last_name = ' '.join(fl[1:])
	if "." in first_name:
		first_initial = first_name
	else:
		first_initial = first_name[0]+"."

	if ((last_name == None) or (last_name == '')):
		last_name = name

	return {'FirstName':first_name, 'FirstInitial':first_initial, 'LastName':last_name}

    
