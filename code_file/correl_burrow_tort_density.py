import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
from datetime import datetime
from datetime import timedelta
import networkx as nx
import math

######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method

######################################################################################
def years_of_observations(filename):
	"""returns a dict of year over which the observation were recorded.
	each key is again defined as a dict"""
	
	cursor = db.cursor()
	query = """select year(date) from """ +filename+ """ group by year(date);"""
	cursor.execute(query)
	results = cursor.fetchall()
	
	year_list = [str(row[0]) for row in results]
	year_dict = {}
	for year in year_list:
		year_dict[year]={}

	return year_dict

######################################################################################
def return_burrow_list(filename, year_dict):
	"""returns the dict of burrows for each year of observation"""
	
	cursor = db.cursor()
	query = """select Burrow_number from """ +filename+ """ group by Burrow_number;"""
	cursor.execute(query)
	results = cursor.fetchall()
	#converting all the names into upper case
	burr_list = [row[0].upper() for row in results]

	# check the life-span of each burrow
	# birthyear = year where the burrow was first mentioned
	#deathyear = year where the burrow was last mentioned
	birthyear = {}
	deathyear = {}
	for burr in burr_list:
		cursor = db.cursor()
		cursor.execute("""select min(year(date)), max(year(date)) from """+filename+""" where Burrow_number = %s;""", (burr))
		results1 = cursor.fetchall()
		birthyear[burr] = results1[0][0]
		deathyear[burr] = results1[0][1]


	
	for year in year_dict.keys():
		for burr in burr_list:
			# include the burrow only when the year is between its birthyear and deathyear.
			if int(year) >= int(birthyear[burr]) and int(year) <= int(deathyear[burr]):
				year_dict[year][burr]=[]
	return year_dict

######################################################################################
def return_tort_list(filename):
	
	"""returns list of tortoises in the data-set"""
	
	cursor = db.cursor()
	query = """select Tortoise_number from """ +filename+ """ group by Tortoise_number;"""
	cursor.execute(query)
	results = cursor.fetchall()
	#converting all the names into upper case
	return [row[0].upper() for row in results]
	
	
#########################################################################################################
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	#files = ["BSV_aggregate"]
	avg_active_burrows = []
	total_torts = []
	for filename in files:
		year_dict = years_of_observations(filename)
		year_dict = return_burrow_list(filename, year_dict)
		tort_list = return_tort_list(filename)
		avg_active_burrows.append(np.mean([len(year_dict[key]) for key in year_dict.keys()]))
		total_torts.append(len(tort_list))
	print ("files = "), files
	print ("avg active burrows"), avg_active_burrows
	print ("total torts"), total_torts
	avg_active_burrows = [math.log(x) for x in avg_active_burrows]
	total_torts = [math.log(x) for x in total_torts]
	plt.xlabel("(Log)Average number of active burrows per year")
	plt.ylabel("(Log) Total number of tortoise recorded")
	plt.plot(avg_active_burrows, total_torts, 'bo')
	plt.show()
