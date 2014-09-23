import MySQLdb as sql
import numpy as np
import csv

######################################################################################

# Open database connection
db = sql.connect("localhost","root","bio123456","burrow_data" )
# prepare a cursor object using cursor() method

######################################################################################
def valid_burrow(burr):
	"""check if the burrow id is valid"""
	
	has_numbers= False
	no_special_chars= True
	
	# split string
	mylist = [burr[num] for num in xrange(0, len(burr))]
	
	# check if there are any numbers i nthe string
	if any(num.isdigit() for num in mylist): has_numbers = True
	if "+" in mylist: no_special_chars = False
	if "?" in mylist: no_special_chars = False
	if "/" in mylist: no_special_chars = False

	return has_numbers and no_special_chars


####################################################################################3
def sample_complete_yearlist(filename):

	""" Considers biological year. consider only those year that have 3/4 of quarters sampled"""	
	
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

def calculate_burrow_local_density(filename, finalbur, yearlist, burr_attr):
	
	"""extract burrow density (ONLY ALIVE BURROW COUNTED) around 100 sq m focal burrow when the burro is alive (including the focal burrow). 
	burrow_density has keys= burrow ids and val = dict with key = year and val = list with burrows that were
	alive around 1 km sq area around the burrow
	ALIVE definition = a burrow is considered to be born at the year where it was first reported. Death is
	considered to by the last year that it was reported. A burrow is considered to be alive between these years"""
	
	burrow_density={}	
	for bur in finalbur:
		easting = burr_attr[bur][3]
		northing = burr_attr[bur][4]
		burrow_density[bur]={}
		for year in yearlist:
			
			# extract all the burrows that have easting+-50 w.r.t focal burrows
			bur_filter1 = [bur1 for bur1 in burr_act.keys() if bur!=bur1 and burr_attr[bur1][3]>=easting-50 and burr_attr[bur1][3]<=easting+50]
			
			# from bur_filter1 extract all the burrows that have northing+-50 w.r.t focal burrows
			bur_filter2 = [bur1 for bur1 in bur_filter1 if bur!=bur1 and burr_attr[bur1][4]>=northing-50 and burr_attr[bur1][4]<= northing+50]
			
			
			# from bur_filter2 extract all burrows that were alive during the year=year, (sorted(burr_act[bur1].keys()))[0] is the first year
			# (sorted(burr_act[bur1].keys()))[-1] is the last year
			bur_filter3 =[bur1 for bur1 in bur_filter2 if (sorted(burr_act[bur1].keys()))[0]<=year<=(sorted(burr_act[bur1].keys()))[-1]]
			
			# bur_filter3 is the final list. Do a len to find out number of alive burrow 
			burrow_density[bur][year] = len(bur_filter3) 
			

	return burrow_density

######################################################################################
def calculate_tort_local_density(filename, finalbur, yearlist, burr_attr):
	"""considered biological year. Extract tort density around 100 sq m of focal burrow when the burro is alive. 
	Tort density is the averge(total (non unique) torts reported around 100 sq m of burrow each day of survey)"""
	
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	tort_density={}	
	for bur in finalbur:
		easting = burr_attr[bur][3]
		northing = burr_attr[bur][4]
		tort_density[bur]={}
		for year in yearlist:
			tort_density[bur][year]={}
			for quarter in quarterdict.keys():
				cursor = db.cursor()
				# extract all torts that have easting+-50 w.r.t focal burrows in that year (March_Dec of that year)
				cursor.execute(""" select  date, count(date) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s group by date;""", (year, ','.join(str(num) for num in quarterdict[quarter]), easting-50, easting+50, northing-50, northing+50))
				results = cursor.fetchall()
				# Do a len to find out number of torts around the burrow in the particular year
				tortlist = [row[1] for row in results]
				if quarter==1:
					cursor = db.cursor()
					# In addition, extract all torts that have easting+-50 w.r.t focal burrows in that year (Jan-Feb of next calender year)
					cursor.execute(""" select  date, count(date)  from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 and UTM_easting>= %s and UTM_easting<=%s and UTM_northing>=%s and UTM_northing<=%s group by date;""", (year+1, ','.join(str(num) for num in [1,2]), easting-50, easting+50, northing-50, northing+50))
					results = cursor.fetchall()
					
					for row in results:
						tortlist.append(row[1])
				
				if len(tortlist) > 0 :tort_density[bur][year][quarter] = np.mean(tortlist)
				else: tort_density[bur][year][quarter] =0
				#print bur, year, quarter, tort_density[bur][year][quarter]
		
	return tort_density
	
######################################################################################
def calculate_bur_distance(filename, burr_act, burr_attr, yearlist):
	
	"""considered biological year"""
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	
	# stores average home range location of the torts at particular quarter of the year
	centr_dict={}
	for year in yearlist:
		centr_dict[year]={}
		for quarter in quarterdict.keys():
				
			##########################
			# Determine the average home range of tortoise sampled the particular time interval of the year
			cursor = db.cursor()
			cursor.execute(""" select UTM_easting, UTM_northing from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 ; """, (year, ','.join(str(num) for num in quarterdict[quarter])))
			results = cursor.fetchall()
			easting_location = [row[0] for row in results if row[0] >0]
			northing_location = [row[1] for row in results if row[1] > 0]
			
			if quarter==1:
				cursor = db.cursor()
				# In addition, extract all torts that have easting+-50 w.r.t focal burrows in that year (Jan-Feb of next calender year)
				cursor.execute(""" select UTM_easting, UTM_northing from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 ; """, (year+1, ','.join(str(num) for num in [1,2])))
				results = cursor.fetchall()
				for row in results:
					if row[0] > 0: easting_location.append(row[0])
					if row[1] >0 : northing_location.append(row[1])
				
			mean_easting = choose_approx_location(easting_location)
			mean_northing = choose_approx_location(northing_location)
			centr_dict[year][quarter] = [mean_easting, mean_northing]
			
	
	##########################
	bur_dist ={}
	for bur in burr_act.keys():
		bur_dist[bur]={}
		for year in burr_act[bur].keys():
			if year in yearlist:
				bur_dist[bur][year]={}
				for quarter in burr_act[bur][year].keys():
				
					# easting and northing location of the burrow
					bur_e = burr_attr[bur][3]
					bur_n = burr_attr[bur][4]
				
					if centr_dict[year][quarter][0] >0 and centr_dict[year][quarter][1] > 0 and bur_e>0 and bur_n >0: 
						bur_dist[bur][year][quarter] = (np.sqrt((bur_e - centr_dict[year][quarter][0])**2 + (bur_n - centr_dict[year][quarter][1])**2))/1000.0
					else: bur_dist[bur][year][quarter] = 'NA'
					#print year, quarter, bur_dist[bur][year][quarter], bur_e, bur_n, centr_dict[year][quarter][0], centr_dict[year][quarter][1]
	return bur_dist

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
			#sample Mar - Nov of that year
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
			if len(list(set(date_list))) <=1: sur_freq[year][quarter] =0
			else:
				# calculate the average interval between the dates sampled
				freq_list = np.mean([abs((date_list[num]-date_list[num+1]).days) for num in xrange(len(date_list)-1)])
				# survey freq = 1/ average interval between the dates sampled
				sur_freq[year][quarter] = 1.0/(1.0*freq_list)
			
			##########################
			
			##########################
			#calculate the proportion of  tortoise sampled each day during that quarter
			#sample Mar - Nov of that year
			cursor = db.cursor()
			cursor.execute( """select date, count(date) from """ + filename + """ where year(date) = %s and find_in_set(month(date), %s)>0 group by date;""",  (year, ','.join(str(num) for num in quarterdict[quarter])))
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
				

######################################################################################
def summarize_burrow_survey(filename, finalbur, yearlist):
	"""Calcuate survey bias w.r.t burrow. Formula - Number of days focal burrow reported / total days of reporting for that quarter"""
	
	##########################
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	##########################
	bursurvey = {}
	for year in yearlist:
		for quarter in quarterdict.keys():
				
			##########################
			cursor = db.cursor()
			#sample number of surveys days for Mar - Dec  of that year
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
			
			for bur in finalbur:
				cursor = db.cursor()
				#sample number of times a burrow was reported days for Mar - Nov of that year
				cursor.execute( """ select date from """ + filename + """ where burrow_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (bur, year, ','.join(str(num) for num in quarterdict[quarter])))
				results1 = cursor.fetchall()
				burlist =[row[0] for row in results1]
				if quarter==1:
					cursor = db.cursor()
					# In addition, extract all entries for Jan-Feb of next calender year
					cursor.execute( """ select date from """ + filename + """ where burrow_number = %s and year(date) = %s and find_in_set(month(date), %s)>0 group by date; """,  (bur, year+1, ','.join(str(num) for num in [1,2])))
					results1 = cursor.fetchall()
					for row in results1: burlist.append(row[0])
				times_bur_sampled = len(burlist)
				
				if not bursurvey.has_key(bur):	bursurvey[bur]={}
				if not bursurvey[bur].has_key(year):	bursurvey[bur][year]={}
				
				bursurvey[bur][year][quarter] = times_bur_sampled/(1.0* total_sampled_dates)
	
	return 	bursurvey				

######################################################################################
def extract_data(filename, yearlist):

	###########################################
	# extract burrow attributes
	burr_attr ={}
	cursor = db.cursor()
	cursor.execute( """  select ucase(Burrow_number), elevation, habitat_clean, soil_clean, UTM_easting, UTM_northing from """ + filename + """  where Burrow_number>"" ; """)
	# execute SQL query using execute() method.
	results = cursor.fetchall()
	
	for row in results:
		burr = row[0]
		if valid_burrow(burr):
			burr_attr[burr] = [row[1], row[2], row[3], row[4], row[5]]
	
	###############################	
	
	# extract burrow yearly activity. burr_act has keys= burrow ids and val = dict with key = year and val = list with torts that 
	# visited the burrow that year
	burr_act ={}
	cursor = db.cursor()
	query = """  select ucase(Burrow_number), ucase(Tortoise_number), year(date), month(date) from """ + filename + """  where Burrow_number>"" and Tortoise_number>"" group by Burrow_number, Tortoise_number, date ;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	
	# Diving year into three quarters. First quarter is Nov, Dec (of same year) Jan, Feb (of next year)
	#Second: March, april, may, june
	#third, July Aug, Sept, Oct
	quarterdict={}
	quarterdict[1] = [11,12]
	quarterdict[2] = [3,4,5,6]
	quarterdict[3] = [7,8,9,10]
	
	for row in results:
		burr = row[0]
		
		# if the sampling is winter months then the year is year-1 (the biological year being considered is from March-Feb of next year)
		if row[3]==1 or row[3]==2:
			year = row[2] - 1
			quarter = 1
		else: 
			# find the quarter
			quarter = [key for key, val in quarterdict.items() if row[3] in val][0]
			year = row[2]
		if valid_burrow(burr):
			if not burr_act.has_key(burr): burr_act[burr] = {}
			if not (burr_act[burr]).has_key(year): burr_act[burr][year]={}
			if not (burr_act[burr][year]).has_key(quarter): burr_act[burr][year][quarter]=[]
			burr_act[burr][year][quarter].append(row[1])		
			burr_act[burr][year][quarter] = list(set(burr_act[burr][year][quarter]))
	
	###############################	
	#count the number of unique tort that visited focal burrow in a particular year's quarter
	for burr in burr_act.keys():
		for year in yearlist:
			if not burr_act[burr].has_key(year): burr_act[burr][year]={}
			for quarter in [1,2,3]:
				if not burr_act[burr][year].has_key(quarter): burr_act[burr][year][quarter]= 0 
				else: burr_act[burr][year][quarter]=len(burr_act[burr][year][quarter])
			
	##############################
	
	return burr_act, burr_attr

######################################################################################
def extract_finalbur_list(fileaname, burr_act, yearlist):

	"""include only those burrows that have reported least during 2 times out of the total survey years (excluding site that were sampled only one year)""" 
	
	finalbur=[]
	for bur in burr_act.keys():
		reportlist=[]
		for year in yearlist:
			for quarter in [1,2,3]:
				reportlist.append(burr_act[bur][year][quarter])

		#print bur, reportlist, 
		if len([num for num in reportlist if num > 0])>1  or len(yearlist)==1: 
			finalbur.append(bur)
			#print ("accept")
		#else: print ("reject")

	
	print ("number of final burrows"), len(finalbur)
	
	return finalbur

######################################################################################
def summarize_burrow_usage(filename, temp, rain, burr_act, burr_attr, tort_density, burrow_density, sur_freq, sur_rate, bursurvey, yearlist, burdist, site):	
	
	for bur in finalbur:
		for year in yearlist:
			if year in yearlist:
				for quarter in [1,2,3]:
					elem1 = [bur, year, quarter, round(temp[year][quarter], 3), round(rain[year][quarter], 3)]
					elem2 = [burr_act[bur][year][quarter]] + [1 if burr_act[bur][year][quarter]>1 else 0]
					easting = burr_attr[bur][3] if burr_attr[bur][3] >0 else 'NA'
					northing = burr_attr[bur][4] if burr_attr[bur][4] >0 else 'NA'				
					elem3 = [tort_density[bur][year][quarter], burrow_density[bur][year], burr_attr[bur][0], burr_attr[bur][1], burr_attr[bur][2], easting, northing, sur_freq[year][quarter], sur_rate[year][quarter], bursurvey[bur][year][quarter], burdist[bur][year][quarter], site] 
					elements = elem1 +elem2+elem3
		
					# replace missing entries with NA
					elements = ["NA" if num=="" else num for num in elements]
					elements = ["NA" if num=="N/A" else num for num in elements]
					elements = ["NA" if num=="nan" else num for num in elements]		
					writer.writerow(elements)
	
########################################################################################################3
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate", "FI_aggregate"]
	#files = ["FI_aggregate"]
	sites = ["BSV", "CS", "HW", "LM", "MC", "PV", "SG", "SL", "FI"]
	
	writer = csv.writer(open('burrow_use_for_regression_YEARBALANCED_ALL.csv','wb'))
	header = ["burrow_number", "year", "quarter", "temperature", "rainfall", "count", "logistic_count", "local_tort_density", "local_burrow_density",  "elevation", "habitat", "soil", "UTM_easting", "UTM_northing", "survey_freq", "survey_rate", "burrow_survey", "burrow_distance", "site"] 
	writer.writerow(header)
	for site, filename in zip(sites, files):
		print filename
		yearlist = sample_complete_yearlist(filename)
		burr_act, burr_attr = extract_data(filename, yearlist)
		finalbur = extract_finalbur_list(filename, burr_act, yearlist)
		temp, rain = calculate_sitespecific_average_climate(filename)
		print ("temperature, rain done")
		tort_density = calculate_tort_local_density(filename, finalbur, yearlist, burr_attr)
		print ("tort density done")
		burrow_density =  calculate_burrow_local_density(filename, finalbur, yearlist, burr_attr)
		print ("burrow density done")
		sur_freq, sur_rate  = calculate_survey_freq_rate(filename, yearlist)
		print ("survey freq and rate done")
		bursurvey = summarize_burrow_survey(filename, finalbur, yearlist)
		print ("burrow survey done")
		burdist = calculate_bur_distance(filename, burr_act, burr_attr, yearlist)
		print ("writing data...")
		summarize_burrow_usage(filename, temp, rain, burr_act, burr_attr, tort_density, burrow_density, sur_freq, sur_rate, bursurvey, yearlist, burdist, site)
