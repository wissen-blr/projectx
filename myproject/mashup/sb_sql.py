from django.db import connection
import logging

# Get an instance of a logger
logger = logging.getLogger("projectx")


#helper function to extract location name from standardized linkedin_location
def strip_location(linkedin_location):
	location = linkedin_location.strip()

	area_index = linkedin_location.upper().find("AREA")
	if area_index != -1:
		location = linkedin_location[0:area_index].strip()

	greater_index = location.upper().find("GREATER")
	if greater_index != -1:
		location = location[greater_index+7:].strip()

	return location



def get_locations(user_id):
	print user_id
	raw_locations_list = execute_query("select mashup_location.name, count( mashup_location.name) from mashup_connection_profile, mashup_location where mashup_location.id = mashup_connection_profile.current_location_id and  mashup_connection_profile.user_id = %s group by mashup_location.name order by count( mashup_location.name) desc" % (user_id))
	location_list = []
	for location_tuple in raw_locations_list:
		location = location_tuple[0]
		location = strip_location(location)
		new_location_tuple = (location, location_tuple[1])
		location_list.append(new_location_tuple)
	return location_list

def get_industries(user_id):
	print user_id
	industry_list = execute_query("select mashup_work_info.industry, count(mashup_work_info.industry) from mashup_connection_profile, mashup_work_info where mashup_work_info.connection_profile_id  = mashup_connection_profile.id and  mashup_connection_profile.user_id = %s group by mashup_work_info.industry order by count( mashup_work_info.industry) desc" % (user_id))
	industry_list = list(industry_list)
	if len(industry_list)>0:
		if industry_list[0][0]=='':
			industry_list.pop(0)
	return industry_list

def get_positions(user_id):
	print user_id
	return execute_query("select mashup_work_info.position, count(mashup_work_info.position) from mashup_connection_profile, mashup_work_info where mashup_work_info.connection_profile_id  = mashup_connection_profile.id and  mashup_connection_profile.user_id = %s group by mashup_work_info.position order by count( mashup_work_info.position) desc" % (user_id))

def execute_query(query):
	cursor = connection.cursor()
	cursor.execute(query)
	return cursor.fetchall()

