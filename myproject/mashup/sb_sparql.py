from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from models import *
import json
from pprint import pprint
import StringIO
import urllib2
import urlparse
import time
from django.db import connection, transaction
import string
import datetime
from rdflib import Namespace
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
from SPARQLWrapper import SPARQLWrapper, JSON
from django.conf import settings
import sys
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger("sbutler")

def execute_sparql(queryString):
	#for results in json
	try:
		#print queryString
		sparql = SPARQLWrapper("http://dbpedia.org/sparql")
		sparql.setQuery(queryString)
		sparql.setReturnFormat(JSON)
		#		ret = sparql.query()
		sparql_results = sparql.query().convert()
		#print results
		result_row = sparql_results["results"]["bindings"]
		if len(result_row) == 0:
			result = None
		else:
			result = result_row = sparql_results["results"]["bindings"][0] #pick first
		return result
	except Exception, e:
		print "Exception:", e
		logger.error(sys.exc_info())

def movie_sparql(movie_name):
	movieString = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX foaf: <http://xmlns.com/foaf/0.1/>
	PREFIX dbpedia: <http://dbpedia.org/resource/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	SELECT ?abs ?film
	WHERE
	{
	  ?film rdf:type dbpedia-owl:Film .
	  ?film dbpedia-owl:abstract ?abs .
	  ?film rdfs:label \"%(movie_name)s\"@en
	  filter (lang(?abs) = "en")
	}
	LIMIT 1
	""" % {'movie_name': movie_name}
	return movieString

def company_sparql(company_name):
	companyString = """
	PREFIX dcterms: <http://purl.org/dc/terms/>
	PREFIX dbpprop: <http://dbpedia.org/property/>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX foaf: <http://xmlns.com/foaf/0.1/>
	PREFIX dbpedia: <http://dbpedia.org/resource/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	SELECT ?company  ?industry ?keyperson ?thumbnail ?abstract
	WHERE
	{
	  ?company rdf:type dbpedia-owl:Company.
	  ?company dbpprop:industry ?industry .
	  ?company dbpprop:keyPeople ?keyperson .
	  ?company dbpedia-owl:thumbnail ?thumbnail .
	  ?company dbpedia-owl:abstract  ?abstract .
	  ?company rdfs:label \"%(company_name)s\"@en .
	  filter (lang(?abstract) = "en")
	}
	LIMIT 1
	""" % {'company_name': company_name}
	return companyString

def interest_sparql(interest_name):
	interestString = """
	PREFIX dbpprop: <http://dbpedia.org/property/>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX foaf: <http://xmlns.com/foaf/0.1/>
	PREFIX dbpedia: <http://dbpedia.org/resource/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	PREFIX yago: <http://dbpedia.org/class/yago/>
	PREFIX dcterms: <http://purl.org/dc/terms/>
	PREFIX category: <http://dbpedia.org/resource/Category:>
	SELECT ?interest ?abstract
	WHERE
	{
	  ?interest rdfs:label \"%(interest_name)s\"@en.
	  ?interest dbpedia-owl:abstract ?abstract
	  filter (lang(?abstract) = "en")
	 }
	LIMIT 1
	""" % {'interest_name': interest_name}
	return interestString

def place_sparql():
	placeString = """
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX foaf: <http://xmlns.com/foaf/0.1/>
	PREFIX dbpedia: <http://dbpedia.org/resource/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	SELECT ?city  ?lat ?long
	WHERE
	{
	  ?city rdf:type dbpedia-owl:City.
	  ?city rdfs:label "Cambridge, Massachusetts"@en .
	  ?city dbpedia-owl:abstract  ?abstract .
	  ?city dbpedia-owl:country  dbpedia:United_States  .
	  ?city geo:lat ?lat .
	  ?city geo:long ?long .
	}
	LIMIT 1
	"""
	return placeString
def hobby_sparql():
	hobbyString = """
	PREFIX dbpprop: <http://dbpedia.org/property/>
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX foaf: <http://xmlns.com/foaf/0.1/>
	PREFIX dbpedia: <http://dbpedia.org/resource/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	PREFIX yago: <http://dbpedia.org/class/yago/>
	PREFIX dcterms: <http://purl.org/dc/terms/>
	PREFIX category: <http://dbpedia.org/resource/Category:>
	SELECT ?hobby ?abstract
	WHERE
	{
	  ?hobby dcterms:subject category:Hobbies.
	  ?hobby rdfs:label "Home movies"@en.
	  ?hobby dbpedia-owl:abstract ?abstract
	  filter (lang(?abstract) = "en")
	}
	LIMIT 1
	"""
	return hobbyString
