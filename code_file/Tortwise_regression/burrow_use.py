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
def extract_burrow_use(filename, sexdict, yearlist):

	"""Considers biological year. extract unique burrow use of the tort in the particular time period of the year"""
	
	##########################
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	buruse ={}
	for tort in sexdict.keys():
		buruse[tort]={}
		for year in yearlist:
			buruse[tort][year]={}
			for quarter in quarterdict.keys():
				cursor = db.cursor()
				cursor.execute( """ select ucase(burrow_number) from """ + filename + """ where tortoise_number = %s and burrow_number> "" and year(date) = %s and find_in_set(month(date), %s)>0 group by burrow_number ; """,  (tort, year, ','.join(str(num) for num in quarterdict[quarter])))
				results = cursor.fetchall()
				buruse_list = [row[0] for row in results]
				# In addition, extract a buruse for Jan-Feb of next calender year)
				if quarter==1:
					cursor = db.cursor()
					cursor.execute( """ select ucase(burrow_number) from """ + filename + """ where tortoise_number = %s and burrow_number> "" and year(date) = %s and find_in_set(month(date), %s)>0 group by burrow_number ; """,  (tort, year+1, ','.join(str(num) for num in [1,2])))
					results = cursor.fetchall()
					for row in results: buruse_list.append(row[0])
				
				
				
				buruse[tort][year][quarter]= len(buruse_list)
				
	#######################################
	# add zeros to missing data
	for tort in sexdict.keys():
		for year in yearlist:
			if not buruse[tort].has_key(year): buruse[tort][year]={}
			for quarter in quarterdict.keys():
				if not buruse[tort][year].has_key(quarter): buruse[tort][year][quarter]= 0 
	
	
	##############################
				
	return buruse
				
######################################################################################
def extract_status(filename, final_tortlist, yearlist):
	"""extract status of tort. If there are multiple status then pick the one with highest freq.
	Biological year considered"""
	
	##########################
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
		
	status ={}
	for tort in final_tortlist:
		status[tort]={}
		for year in yearlist:
			status[tort][year]={}
			for quarter in quarterdict.keys():
				cursor = db.cursor()
				cursor.execute( """ select Tortoise_status from """ + filename + """ where tortoise_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 ; """,  (tort, year, ','.join(str(num) for num in quarterdict[quarter])))
				results = cursor.fetchall()
				statuslist = [row[0] for row in results]
				
				##################################
				#add data from Jan-Feb of the next year
				if quarter==1:
					cursor = db.cursor()
					cursor.execute( """ select Tortoise_status from """ + filename + """ where tortoise_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 ; """,  (tort, year+1, ','.join(str(num) for num in [1,2])))
					results = cursor.fetchall()
					statuslist= statuslist + [row[0] for row in results]
				
				##################################
				#check if list is empty and if list contains None values
				if len(statuslist)>0 and list(set(statuslist))[0]!=None:
					status[tort][year][quarter] = max(set(statuslist), key=statuslist.count)
				else: status[tort][year][quarter] = 'NA'
	return status

######################################################################################
def extract_temporal_location(filename,final_tortlist, yearlist):
	""" extract std home range of the animals"""

	#tortdata[year][quarter] = [avg homerange, std homerange]
	
	##########################
	quarterdict={}
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
		
	tortdata={}
	for tort in final_tortlist:
		tortdata[tort]={}
		for year in yearlist:
			tortdata[tort][year]={}
			for quarter in quarterdict.keys():
				#in case the tort was not reported in the particular quarter
				tortdata[tort][year][quarter] = 'NA'
				cursor = db.cursor()
				cursor.execute( """ select UTM_easting, UTM_northing from """ + filename + """ where tortoise_number = %s and year(date) = %s and find_in_set(month(date), %s)>0  and  UTM_easting > 0 and UTM_northing >0 ; """,  (tort, year, ','.join(str(num) for num in quarterdict[quarter])))
				results = cursor.fetchall()
				
				for row in results:
					tort_easting_location =  choose_approx_tort_location([row[0] for row in results if row[0] > 0])
					tort_northing_location = choose_approx_tort_location([row[1] for row in results if row[1] > 0 ])
					
					if len(tort_easting_location) > 0 and len(tort_northing_location) > 0 : 
						std_home = np.mean([np.std([loc/1000.0 for loc in tort_easting_location]), np.std([loc/1000.0 for loc in tort_northing_location])])
					
						tortdata[tort][year][quarter] = std_home
			
						
			
			
			
			################################################################################
			# send separate query for the winter month
			#############
			#calculate average home range of all the tort in the quarter
			tortdata[tort][year][1] = 'NA'
			cursor = db.cursor()
			cursor.execute( """ select  UTM_easting, UTM_northing from """ + filename + """ where tortoise_number = %s and ((year(date)= %s and (month(date)=11 or month(date)=12)) or (year(date)=%s and (month(date)=1 or month(date)=2))) and  UTM_easting > 0 and UTM_northing > 0 ; """,  (tort, year, year+1))
			results = cursor.fetchall()
			for row in results:
					tort_easting_location =  choose_approx_tort_location([row[0] for row in results if row[0] > 0])
					tort_northing_location = choose_approx_tort_location([row[1] for row in results if row[1] > 0 ])
					if len(tort_easting_location) > 0 and len(tort_northing_location) > 0 : 
						std_home = np.mean([np.std([loc/1000.0 for loc in tort_easting_location]), np.std([loc/1000.0 for loc in tort_northing_location])])
						tortdata[tort][year][1] =  std_home
					
			################################################################################
				
	return tortdata



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
def calculate_burrow_local_density(filename, final_tortlist, yearlist):
	
	"""extract burrow density (ONLY ALIVE BURROW COUNTED) around 100 sq m of tort when the burrow is alive. 
	burrow_density has keys= burrow ids and val = dict with key = year and val = list with burrows that were
	alive around 1 km sq area around the burrow
	ALIVE definition = a burrow is considered to be born at the year where it was first reported. Death is
	considered to by the last year that it was reported. A burrow is considered to be alive between these years"""
	
	##########
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	##############
	
	burloc, burdata = extract_burrow_data(filename)
	final_burrow_density ={}	
	for focaltort in final_tortlist:
		burrow_density={}
		##################################calculate burrow density
		final_burrow_density[focaltort] ={}
		cursor = db.cursor()
		cursor.execute( """  select date, UTM_easting, UTM_northing from """ + filename + """  where Tortoise_number = %s group by date ;""", (focaltort))
		# Fetch all the rows in a list of lists.
		results = cursor.fetchall()
		
		for row in results:
			date = str(row[0])
			easting = row[1]
			northing = row[2]
			splitdate = date.split("-")
			year = int(splitdate[0])
			
			# extract all the burrows that have easting+-50 w.r.t focal tort location
			bur_filter1 = [bur1 for bur1 in burloc.keys() if  burloc[bur1][0]>=easting-50 and burloc[bur1][0]<=easting+50]
			
			# from bur_filter1 extract all the burrows that have northing+-50 focal tort location
			bur_filter2 = [bur1 for bur1 in bur_filter1 if burloc[bur1][1]>=northing-50 and burloc[bur1][1]<= northing+50]
			
			
			# from bur_filter2 extract all burrows that were alive during the year=year, (sorted(burdata[bur1].keys()))[0] is the first year
			# (sorted(burdata[bur1].keys()))[-1] is the last year
			bur_filter3 =[bur1 for bur1 in bur_filter2 if (sorted(burdata[bur1].keys()))[0]<=year<=(sorted(burdata[bur1].keys()))[-1]]
			
			# bur_filter3 is the final list. Do a len to find out number of alive burrow
			burrow_density[date] = len(bur_filter3)
			
			
		
		for year in yearlist:
			if not final_burrow_density[focaltort].has_key(year): final_burrow_density[focaltort][year] ={}
	    		for quarter in quarterdict.keys():
				keylist = [key for key in burrow_density.keys() if int(key.split("-")[0])== year and int(key.split("-")[1]) in quarterdict[quarter]]
				#in addition, consider jan Feb of next year for Q1 of previous year
				if quarter==1: 
					additional_key = [key for key in burrow_density.keys() if int(key.split("-")[0])== year+1 and int(key.split("-")[1]) in [1,2]]
					keylist = keylist + additional_key
		
				final_burrow_density[focaltort][year][quarter] = np.mean([burrow_density[date] for date in keylist])
						
		
	return final_burrow_density

######################################################################################
def calculate_tort_local_density(filename, final_tortlist, yearlist):

	##########
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	##############

	final_tort_density ={}
	for focaltort in final_tortlist:
		final_tort_density[focaltort] ={}
		tort_density={}
		##################################calculate tort density
		cursor = db.cursor()
		cursor.execute( """  select date, UTM_easting, UTM_northing from """ + filename + """  where Tortoise_number = %s group by date ;""", (focaltort))
		# Fetch all the rows in a list of lists.
		results = cursor.fetchall()
		
		for row in results:
			date = str(row[0])
			easting = row[1]
			northing = row[2]
			splitdate = date.split("-")
			year = int(splitdate[0])
			
			cursor = db.cursor()
			cursor.execute( """  select Tortoise_number from """ + filename + """  where Tortoise_number != %s and date=%s and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s ; """, (focaltort, date,  easting-50, easting+50, northing-50, northing+50))
			# Fetch all the rows in a list of lists.
			results = cursor.fetchall()
			#extract list of all torts that were within 100 sq m of focal tort were on that particular date
			othertort = [row[0] for row in results]
			tort_density[date] = len(othertort) 
			
			######################################################
		
		for year in yearlist:
			if not final_tort_density[focaltort].has_key(year): final_tort_density[focaltort][year] ={}
	    		for quarter in quarterdict.keys():
				keylist = [key for key in tort_density.keys() if int(key.split("-")[0])== year and int(key.split("-")[1]) in quarterdict[quarter]]
				#in addition, consider jan Feb of next year for Q1 of previous year
				if quarter==1: 
					additional_key = [key for key in tort_density.keys() if int(key.split("-")[0])== year+1 and int(key.split("-")[1]) in [1,2]]
					keylist = keylist + additional_key
		
				final_tort_density[focaltort][year][quarter] = np.mean([tort_density[date] for date in keylist])
			
			
			
	return final_tort_density		

######################################################################################
def calculate_sitespecific_average_climate(filename):
		
	"""considered biological year"""
	##########################
	quarterdict={}
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	temp_raw={}
	rain_raw={}
	cursor = db.cursor()
	cursor.execute(""" select year(date), month(date), climate_temperature, climate_rainfall from """ + filename + """ group by year(date), month(date) """)
	results = cursor.fetchall()
	for row in results:
		year = row[0]
		month = row[1]
		temperature = row[2]
		rainfall = row[3]
		if not temp_raw.has_key(year): temp_raw[year]={}
		if not rain_raw.has_key(year): rain_raw[year]={}
		temp_raw[year][month]= temperature
		rain_raw[year][month]= rainfall
	
		
	temp={}
	rain={}
	for year in temp_raw.keys():
		if not temp.has_key(year): temp[year]={}
		if not rain.has_key(year): rain[year]={}
		for quarter in quarterdict.keys():
			temp[year][quarter] = np.mean([val for key, val in temp_raw[year].items() if key in quarterdict[quarter] and val is not None])	
			rain[year][quarter] = np.mean([val for key, val in rain_raw[year].items() if key in quarterdict[quarter] and val is not None])
		# calacluate average winter climate in terms of biological year
		if temp.has_key(year+1): winter_temp = [temp_raw[year].get(11), temp_raw[year].get(12), temp_raw[year+1].get(1), temp_raw[year+1].get(2)]
		# if year+1 is not available, take only values for Nov and Dec
		else:  winter_temp = [temp_raw[year].get(11), temp_raw[year].get(12)]
		if rain.has_key(year+1): winter_rain = [rain_raw[year].get(11), rain_raw[year].get(12), rain_raw[year+1].get(1), rain_raw[year+1].get(2)]
		else: winter_rain = [rain_raw[year].get(11), rain_raw[year].get(12)]
		temp[year][1] = np.mean([val for val in winter_temp if val is not None])
		rain[year][1] = np.mean([val for val in winter_rain if val is not None])
	return temp, rain
			
######################################################################################
def calculate_survey_freq_rate(filename, yearlist):
	
	"""considered biological year"""
	##########################
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	# Determine the total number of torts ever sampled at the site
	cursor = db.cursor()
	cursor.execute(""" select tortoise_number from """ + filename + """ group by tortoise_number;""")
	results = cursor.fetchall()
	tot_torts = len([row[0] for row in results])
	
	sur_freq = {}
	sur_rate ={}
	for year in yearlist:
		sur_freq[year]={}
		sur_rate[year] ={}
		for quarter in quarterdict.keys():
				
			##########################
			cursor = db.cursor()
			cursor.execute( """ select date from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year, ','.join(str(num) for num in quarterdict[quarter])))
			results = cursor.fetchall()
			date_list =[row[0] for row in results]
			
			if quarter==1:
				cursor = db.cursor()
				# In addition, extract all entries for Jan-Feb of next calender year
				cursor.execute( """ select date from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year+1, ','.join(str(num) for num in [1,2])))
				results = cursor.fetchall()
				for row in results: date_list.append(row[0])
			# sorting dates
			date_list.sort()
			# calculate the average interval between the dates sampled
			freq_list = np.mean([abs((date_list[num]-date_list[num+1]).days) for num in xrange(len(date_list)-1)])
			# survey freq = 1/ average interval between the dates sampled
			sur_freq[year][quarter] = 1.0/(1.0*freq_list)
			##########################
				
			##########################
			#calculate the proportion of  tortoise sampled each day during that quarter
			cursor = db.cursor()
			cursor.execute( """select date, count(date) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year, ','.join(str(num) for num in quarterdict[quarter])))
			results = cursor.fetchall()
			sampled_dates = [row[1] for row in results]
				
			#sample Nov-Feb of previous year
			if quarter==1:
				cursor = db.cursor()
				# In addition, extract all entries for Jan-Feb of next calender year
				cursor.execute( """select date, count(date) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date;""",  (year+1, ','.join(str(num) for num in [1,2])))
				results = cursor.fetchall()
				for row in results: sampled_dates.append(row[1])
			
			# sampling rate = fraction of torts that were surveyed per day during that time interval
			tort_sampled = np.mean([num/(1.0*tot_torts) for num in sampled_dates])
			sur_rate[year][quarter] = tort_sampled
			##########################
	
	return sur_freq, sur_rate
				


###########################################################################################################################################################################
def summarize_tortoise_survey(filename, final_tortlist, yearlist):
	"""Calcuate survey bias w.r.t tort. Formula - Number of days focal tort reported / total days of reporting for that quarter"""
	
	##########################
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	tortsurvey = {}
	for year in yearlist:
		for quarter in quarterdict.keys():
				
			##########################
			cursor = db.cursor()
			#sample number of surveys days for Mar - Dec of that year
			cursor.execute( """ select date from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year, ','.join(str(num) for num in quarterdict[quarter])))
			results = cursor.fetchall()
			date_list =[row[0] for row in results]
			if quarter==1:
				cursor = db.cursor()
				# In addition, extract all entries for Jan-Feb of next calender year
				cursor.execute( """ select date from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (year+1, ','.join(str(num) for num in [1,2])))
				results = cursor.fetchall()
				for row in results: date_list.append(row[0])
				
			total_sampled_dates = len(date_list)
			
			##########################
			
			for tort in final_tortlist:
				
				cursor = db.cursor()
				#sample number of times a burrow was reported days for Mar - Nov of that year
				cursor.execute( """ select date from """ + filename + """ where tortoise_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (tort, year, ','.join(str(num) for num in quarterdict[quarter])))
				results1 = cursor.fetchall()
				tortlist =[row[0] for row in results1]
				if quarter==1:
					cursor = db.cursor()
					# In addition, extract all entries for Jan-Feb of next calender year
					cursor.execute( """ select date from """ + filename + """ where tortoise_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (tort, year+1, ','.join(str(num) for num in [1,2])))
					results1 = cursor.fetchall()
					for row in results1: tortlist.append(row[0])
				times_tort_sampled = len(tortlist)
				
				if not tortsurvey.has_key(tort):	tortsurvey[tort]={}
				if not tortsurvey[tort].has_key(year):	tortsurvey[tort][year]={}
				
				tortsurvey[tort][year][quarter] = times_tort_sampled/(1.0* total_sampled_dates)
	
	return 	tortsurvey				

######################################################################################

def sample_complete_yearlist(filename):

	""" Considers biological year. consider only those year that have 3/4 of the quarters sampled"""	
	
	yeardict={}
	yearlist = []
	############################33
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	# estimate the number of years sampled
	cursor = db.cursor()
	cursor.execute(""" select year(date), month(date) from """ + filename + """ where burrow_number> "" group by year(date), month(date) ;""")
	results = cursor.fetchall()
	
	for row in results:
		month = row[1]
		# if the month is Jan/Feb consider it for the previos year (biological year is from Mar- next Feb)
		if month==1 or month==2:
			year = row[0] -1
		else:
			year = row[0]
		if not yeardict.has_key(year): yeardict[year]=[]
		yeardict[year].append(month)
		# remove repeat instances of quarter
		yeardict[year] = list(set(yeardict[year]))
	
	for year in yeardict.keys():
		reported_Q2 = [num in yeardict[year] for num in [3,4,5,6]]
		reported_Q3 = [num in yeardict[year] for num in [7,8,9,10]]
		reported_Q1 = [num in yeardict[year] for num in [11,12,1,2]]
		 
		if reported_Q2.count(True)>=2 and reported_Q1.count(True)>=2 and reported_Q1.count(True)>=2: yearlist.append(year)
		
	##########################
	print yeardict
	print yearlist
	return yearlist

	
	

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

####################################################################################
def select_final_tortlist(sexdict, yearlist, buruse):

	"""include only those torts that have been eported least during 2 quarters during final yearlist (excluding site that were sampled ony one year) """
	
	finaltort=[]
	for tort in sexdict.keys():
		reportlist=[]
		for year in yearlist:
			if buruse[tort].has_key(year):
				for quarter in buruse[tort][year].keys():
					reportlist.append(buruse[tort][year][quarter])
		if len([num for num in reportlist if num>0]) > 1 or len(yearlist)==1: finaltort.append(tort)
	
	print ("number of final torts="), len(finaltort)
	
	return finaltort
	

######################################################################################
def write_data(site, final_tortlist, sexdict, yearlist, temp, rain, sur_freq, sur_rate, tort_loc, tort_status, buruse, local_tort_density, local_burrow_density, tortsurvey):
	
	
	for tort in final_tortlist:
		for year in yearlist:
			for quarter in [1,2,3]:
				
				elem1 = [site, tort, sexdict[tort], year, quarter, tort_status[tort][year][quarter], temp[year][quarter], rain[year][quarter]]
				elem2 = [local_tort_density[tort][year][quarter], local_burrow_density[tort][year][quarter],  tort_loc[tort][year][quarter]]
				elem3 = [sur_freq[year][quarter] , sur_rate[year][quarter], tortsurvey[tort][year][quarter]]
				elem4 =  [buruse[tort][year][quarter]] + [1 if buruse[tort][year][quarter]>1 else 0]
				elements = elem1 +elem2+elem3 +elem4
		
				# replace missing entries with NA
				elements = ["NA" if num=="" else num for num in elements]
				elements = ["NA" if num=="N/A" else num for num in elements]		
				writer.writerow(elements)
				

#########################################################################################################
if __name__ == "__main__":
	
	#####################################################################
	# writing a csv file
	writer = csv.writer(open('burrow_use.csv','wb'))
	header = ["site", "tortid", "sex", "year", "quarter", "status",  "temperature", "rainfall", "local_tort_density", "local_burrow_density", "std_homerange", "survey_rate", "survey_freq", "tort_survey", "burrow_count", "logistic_count"] 
	writer.writerow(header)
	######################################################################
	
	files = ["BSV_aggregate", "CS_aggregate", "HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate", "FI_aggregate"]
	sites = ["BSV", "CS", "HW", "LM", "MC", "PV", "SG", "SL", "FI"]
	for filename, site in zip(files, sites):
		print filename
		temp, rain = calculate_sitespecific_average_climate(filename)
		sexdict = extract_sex(filename)
		yearlist = sample_complete_yearlist(filename)
		buruse = extract_burrow_use(filename, sexdict, yearlist)
		final_tortlist= select_final_tortlist(sexdict, yearlist, buruse)
		local_tort_density = calculate_tort_local_density(filename, final_tortlist, yearlist)
		print ("done tort density")
		local_burrow_density = calculate_burrow_local_density(filename, final_tortlist, yearlist)
		print ("done burrow density")
		sur_freq, sur_rate  = calculate_survey_freq_rate(filename, yearlist)
		print ("done survey freq and rate")
		tortsurvey = summarize_tortoise_survey(filename, final_tortlist, yearlist)
		print ("done tort survey")
		tort_loc =  extract_temporal_location(filename, final_tortlist, yearlist)
		print ("done tort loc")
		tort_status = extract_status(filename, final_tortlist, yearlist)
		print ("writing")
		write_data(site, final_tortlist, sexdict, yearlist, temp, rain, sur_freq, sur_rate, tort_loc, tort_status, buruse, local_tort_density, local_burrow_density, tortsurvey)
