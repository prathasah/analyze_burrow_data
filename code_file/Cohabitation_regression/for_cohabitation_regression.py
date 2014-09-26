import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
from datetime import datetime
from datetime import timedelta
import networkx as nx
from pylab import *
import csv

# July7 2014: Added temporal analysis to burrow_usage

######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method

######################################################################################
def choose_approx_tort_location(location_list):
	"""Chooses an approximate location by first removing the outliers and then taking an average of 
	the remaining locations"""
	
	#look for the length of location
	countlength = [len(str(loc)) for loc in location_list]
	#pick the most common location size
	length = max(set(countlength), key=countlength.count)	
	#remove all entries whose length do not match up
	for num in location_list:
		if len(str(num))!=length: location_list.remove(num)
	
	avg = np.mean(location_list)
	std = np.std(location_list)
	
	for num in location_list: 
		# remove outliers
		if (num -avg) > 0.5* std: location_list.remove(num)
	return (location_list)


######################################################################################
def choose_approx_location(location_list):
	"""Chooses an approximate location by first removing the outliers and then taking an average of 
	the remaining locations"""
	
	avg = np.mean(location_list)
	std = np.std(location_list)
	
	for num in location_list: 
		# remove outliers
		if (num -avg) > 0.5* std: location_list.remove(num)
	return (np.mean(location_list))

###########################################################################################
def extract_burrow_use(filename, sexdict):

	"""Considers cohabitation event reported each day. Extract total tortoises that the folca tort cohabitated with"""

	cohab ={}
	for tort in sexdict.keys():
		cursor = db.cursor()
		cursor.execute( """ select ucase(burrow_number), date from """ + filename + """ where tortoise_number = %s and burrow_number> "" group by date ; """,  (tort))
		results = cursor.fetchall()
		buruse_list = [(row[0], row[1]) for row in results]
		if len(buruse_list)>0 : cohab[tort] ={}
		for bur, date in buruse_list:
			cursor = db.cursor()
			cursor.execute("""select distinct(Tortoise_number) from """ + filename + """ where Burrow_number = %s and Date = %s and Tortoise_number!= %s; """, (bur, date, tort))
			results = cursor.fetchall()
			cohab[tort][date]= len([row for row in results])
					
	return cohab
				
######################################################################################
def extract_status(filename, tort_location):
	"""extract status of tort on that day"""
	
	status ={}
	for focaltort in tort_location:
		status[focaltort]={}
		cursor = db.cursor()
		tup_datelist =  tuple(["{0}".format(date) for date in tort_location[focaltort].keys()])
		if len(tup_datelist)==1: tup_datelist = str(tup_datelist)[0:-2]+ ")"
		#print focaltort, tort_location[focaltort].keys()
		#print tup_datelist
		cursor.execute( """ select date, Tortoise_status from """ + filename + """ where tortoise_number = %s and date in """ + str(tup_datelist) + """ group by date; """,  (focaltort))
		results = cursor.fetchall()
		for row in results:
			status[focaltort][row[0]] = row[1]
		
				
	for tort in tort_location.keys():
		for date in tort_location[tort].keys():
			#check if status is present or if it is none
			if not status[tort].has_key(date) or  status[tort][date]==None:
					status[tort][date] = 'NA'
			
	return status
#cursor.execute( """select date, count(date) from """ + filename + """ where date in """ + str(tup_datelist) + """ group by date; """)

######################################################################################	
def  extract_burrow_data(filename):
	
	###########################################
	#extract info about burrow's location
	burloc={}
	cursor = db.cursor()
	query = """  select ucase(Burrow_number), UTM_easting, UTM_northing from """ + filename + """  where Burrow_number>"" group by Burrow_number;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	results = cursor.fetchall()
	
	for row in results:
		bur = row[0]
		burloc[bur] = [row[1], row[2]]
	###############################	
	
	# extract burrow list and info. about its "birth" and "death"
	burdata ={}
	cursor = db.cursor()
	query = """  select ucase(Burrow_number), year(date), month(date) from """ + filename + """  where Burrow_number>"" group by Burrow_number, year(date), month(date) ;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	
	# Diving year into three quarters. First quarter is Nov, Decm Jan, Feb
	#Second: March, april, may, june
	#third, July Aug, Sept, Oct
	quarterdict={}
	quarterdict[1] = [11,12,1,2]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	for row in results:
		burr = row[0]
		year = row[1]
		# find the year's quarter
		quarter = [key for key, val in quarterdict.items() if row[2] in val][0]
		if not burdata.has_key(burr): burdata[burr] = {}
		if not (burdata[burr]).has_key(year): burdata[burr][year]=[]
		burdata[burr][year].append(quarter)
		#removing all the repeats of quarter
		burdata[burr][year] = list(set(burdata[burr][year]))		
	
	
	return burloc, burdata
######################################################################################
def calculate_burrow_local_density(filename, cohab):
	
	"""extract burrow density (ONLY ALIVE BURROW COUNTED) around 100 sq m of tort when each day the 
	tort is reported using a burrow. 
	burrow_density has keys= burrow ids and val = dict with key = date and val = number of alive burrows that were
	alive around 100 m sq area around the burrow
	ALIVE definition = a burrow is considered to be born at the year where it was first reported. Death is
	considered to by the last year that it was reported. A burrow is considered to be alive between these years"""

	
	burloc, burdata = extract_burrow_data(filename)
	burrow_density ={}	
	for focaltort in tort_location.keys():
		burrow_density[focaltort]={}
		for date in tort_location[focaltort].keys():
			
			easting = tort_location[focaltort][date][0]
			northing = tort_location[focaltort][date][1]
			year = date.year
			# extract all the burrows that have easting+-50 w.r.t focal tort location
			bur_filter1 = [bur1 for bur1 in burloc.keys() if  burloc[bur1][0]>=easting-50 and burloc[bur1][0]<=easting+50]
			
			# from bur_filter1 extract all the burrows that have northing+-50 focal tort location
			bur_filter2 = [bur1 for bur1 in bur_filter1 if burloc[bur1][1]>=northing-50 and burloc[bur1][1]<= northing+50]
			
			
			# from bur_filter2 extract all burrows that were alive during the year=year, (sorted(burdata[bur1].keys()))[0] is the first year
			# (sorted(burdata[bur1].keys()))[-1] is the last year
			bur_filter3 =[bur1 for bur1 in bur_filter2 if (sorted(burdata[bur1].keys()))[0]<=year<=(sorted(burdata[bur1].keys()))[-1]]
			
			# bur_filter3 is the final list. Do a len to find out number of alive burrow
			burrow_density[focaltort][date] = len(bur_filter3)
			
						
		
	return burrow_density

######################################################################################
def calculate_tort_local_density(filename, tort_location):
	""" Returns the number of unique torts that were within 100 sq. m . f the focal tort each day the tort was reported using the burrow"""

	tort_density ={}	
	for focaltort in tort_location.keys():
		tort_density[focaltort]={}
		for date in tort_location[focaltort].keys():
			easting = tort_location[focaltort][date][0]
			northing = tort_location[focaltort][date][1]
			#Fetch list of all other torts that were present within 100 sq m of the focal tort
			cursor = db.cursor()
			cursor.execute( """  select distinct(Tortoise_number) from """ + filename + """  where Tortoise_number != %s and date=%s and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s group by Tortoise_number; """, (focaltort, date,  easting-50, easting+50, northing-50, northing+50))
			# Fetch all the rows in a list of lists.
			results = cursor.fetchall()
			#extract list of all torts that were within 100 sq m of focal tort were on that particular date
			othertort = [row[0] for row in results]
			tort_density[focaltort][date] = len(othertort) 
			
			#####################################################			
			
	return tort_density		

######################################################################################
def extract_tort_location(filename, cohab):

	"""Extract location of focal tort each day it was reported using a burrow"""
	
	tort_location ={}
	for focaltort in cohab.keys():
		tort_location[focaltort] ={}
		for date in cohab[focaltort].keys():
			##################################calculate tort density
			cursor = db.cursor()
			cursor.execute( """  select  UTM_easting, UTM_northing from """ + filename + """  where Tortoise_number = %s and date =%s ;""", (focaltort, date))
			# Fetch all the easting and northing location of the tort on that day.
			results = cursor.fetchall()
			easting = results[0][0]
			northing = results[0][1]
			
			tort_location[focaltort][date] = (easting,northing)
	
	return tort_location

######################################################################################
def calculate_sitespecific_average_climate(filename, tort_location):
		
	 
	temp={}
	rain={}
	
	#extract all the dates that any tortoise was every reported in a burrow --> makes the computation faster rather than doing it tortwise
	datelist = list(set([date for tort in tort_location.keys() for date in tort_location[tort].keys()]))
	
	cursor = db.cursor()
	tup_datelist =  tuple(["{0}".format(date) for date in datelist])
	if len(tup_datelist)==1: tup_datelist = str(tup_datelist)[0:-2]+ ")"
	cursor.execute( """select date, climate_temperature, climate_rainfall from """ + filename + """ where date in """ + str(tup_datelist) + """ group by date; """)
	results = cursor.fetchall()
	for row in results:
		date = row[0]
		temperature = row[1]
		rainfall = row[2]
		temp[date]= temperature
		rain[date]= rainfall
	
	return temp, rain

###########################################################################################################################################################################
def summarize_tortoise_survey(filename, tort_location):
	"""Calcuate survey rate of all the instances where any tort was reported using a burrow. Survey rate is the proportion of tortoise sampled in that year that were reported that day"""
	
	survey_rate = {}
	daily_sampling={}
	yearly_sampling={}
	
	#extract all the dates that any tortoise was every reported in a burrow --> makes the computation faster rather than doing it tortwise
	datelist = list(set([date for tort in tort_location.keys() for date in tort_location[tort].keys()]))
	
	#extract all the torts that were sampled on the dates in datelist
	cursor = db.cursor()
	tup_datelist =  tuple(["{0}".format(date) for date in datelist])
	if len(tup_datelist)==1: tup_datelist = str(tup_datelist)[0:-2]+ ")"
	cursor.execute( """select date, count(distinct(Tortoise_number)) from """ + filename + """ where date in """ + str(tup_datelist) + """ group by date; """)
	results = cursor.fetchall()
	for row in results: daily_sampling[row[0]] = row[1]
	
	#extract total torts that were sample each year (NOTE THIS YEAR IS CALENDER YEAR)
	cursor = db.cursor()
	cursor.execute( """select year(date), count(distinct(Tortoise_number)) from """ + filename + """  group by year(date)  """, )
	results = cursor.fetchall()
	for row in results:
		yearly_sampling[row[0]]=row[1]
	
		
	for date in datelist:
		year = date. year
		survey_rate[date] = daily_sampling[date]/(1.0*yearly_sampling[year])
		
	
	return 	survey_rate				

	

######################################################################################
def extract_sex(filename):
	""" extract sex info of the animal. Select those that have a known sex. This dict keys 
		now becomes the parent tort list for all data extraction"""
	sexdict={}
	cursor = db.cursor()
	query = """  select ucase(Tortoise_number), sex from """ + filename + """  where Tortoise_number>"" and sex >"" group by Tortoise_number;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	results = cursor.fetchall()
	
	for row in results:
		tort = row[0]
		sex = row[1]
		sexdict[tort] = sex if sex!="?" else 'NA'
	
	return sexdict	


######################################################################################
def write_data(site, sexdict, cohab, tort_location, temp, rain, local_tort_density, local_burrow_density, survey_rate, tort_status):
	
	####
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	####
	for tort in tort_location.keys():
		for date in tort_location[tort].keys():
			month = date.month
			raw_year = date.year
			if month==1 or month==2:
				year = raw_year-1
				quarter = 1
			else:
				# find the quarter
				
				quarter = [key for key, val in quarterdict.items() if month in val][0]
				year = raw_year
				
			elem1 = [site, tort, sexdict[tort], tort_status[tort][date], year, quarter, date, cohab[tort][date]]
			elem2 = [1 if cohab[tort][date]>0 else 0]
			elem3 = [temp[date], rain[date]]
			elem4 = [local_tort_density[tort][date], local_burrow_density[tort][date], survey_rate[date]]
			elements = elem1 +elem2+elem3 +elem4
		
			# replace missing entries with NA
			elements = ["NA" if num=="" else num for num in elements]
			elements = ["NA" if num=="N/A" else num for num in elements]
			elements = ["NA" if num=="nan" else num for num in elements]		
			
			writer.writerow(elements)
				

#########################################################################################################
if __name__ == "__main__":
	
	#####################################################################
	# writing a csv file
	writer = csv.writer(open('cohabitation_regression.csv','wb'))
	header = ["site", "tortid", "sex" , "status", "year", "quarter", "date", "cohab_count", "logistic_count", "temperature", "rainfall", "local_tort_density", "local_burrow_density", "survey_rate"] 
	writer.writerow(header)
	######################################################################
	
	files = ["BSV_aggregate", "CS_aggregate", "HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate", "FI_aggregate"]
	sites = ["BSV", "CS", "HW", "LM", "MC", "PV", "SG", "SL", "FI"]
	for filename, site in zip(files, sites):
		print filename
		
		sexdict = extract_sex(filename)
		print ("done sexdict")
		cohab = extract_burrow_use(filename, sexdict)
		print ("done cohab extraction")
		tort_location = extract_tort_location(filename, cohab)
		print ("done tort location")
		tort_status = extract_status(filename, tort_location)
		temp, rain = calculate_sitespecific_average_climate(filename, tort_location)
		print ("done temp and rain")
		survey_rate = summarize_tortoise_survey(filename, tort_location)
		print ("done tort survey")
		local_burrow_density = calculate_burrow_local_density(filename, tort_location)
		print ("done burrow density")
		local_tort_density = calculate_tort_local_density(filename, tort_location)
		print ("done tort density")
		
		print ("writing")
		write_data(site, sexdict, cohab, tort_location, temp, rain, local_tort_density, local_burrow_density, survey_rate, tort_status)
