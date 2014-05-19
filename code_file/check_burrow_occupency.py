import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
from datetime import datetime
from datetime import timedelta
import networkx as nx

######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method

######################################################################################
def overall_burrow_occupancy_by_year(filename, year_dict):

	cursor = db.cursor()
	query = """select Burrow_number, Tortoise_number, year(Date), count(Burrow_number) from """ +filename+ """ where Burrow_number>"" group by Burrow_number, Tortoise_number, year(Date); """
	cursor.execute(query)
	results = cursor.fetchall()
	
	for row in results:
		#year_dict[year][burrow number] = [list of tortoises that visited the burrow (including repeats)]
		#print row[0], str(row[2])
		year_dict[str(row[2])][row[0].upper()].append(row[1]) 
		
	#removing repeat of burrow visitation and counting the number of animals that visited the burrow in the particular year
	burrow_occupancy= {}
	for year in year_dict.keys():
		burrow_occupancy[year] = []
		for burr in year_dict[year].keys():
			#count the number of unique torts that visited the burrow in a particular year
			burrow_occupancy[year].append(len(set(year_dict[year][burr])))
	
	return burrow_occupancy

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
def plot_burrow_occupancy(burrow_occupancy, filename, year_dict):
	
	bin_list = [x for x in xrange(20)]
	occupancy_list = []
	plt.clf()
	for year in burrow_occupancy.keys():
		occupancy = burrow_occupancy[year]
		counts, bin_edges  = np.histogram(occupancy, bins = bin_list)
		#converting the histogram to percentages
		occupancy_list.append(list([num*100/(1.0*len(year_dict[year])) for num in counts]))
		
		
	
	ylist = [np.mean(num) for num in zip(*occupancy_list)]
	err_list = [np.std(num)/(1.0*np.sqrt(len(num))) for num in zip(*occupancy_list)]
	xaxis = [x for x in xrange(19)]
	plt.bar(xaxis, ylist, yerr = err_list, ecolor = "k", align = "center")
	plt.title ("Avg # of tortoises that visited a burrow in a year, Site = " + filename)
	plt.xlabel("Number of unique tortoises")
	plt.ylabel ("% burrows(out of total <alive> burrows)visited by x no. of unique torts")
	plt.xlim([-1, 20])
	plt.savefig("Burrow_occupancy_"+filename)


#########################################################################################################
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	#files = ["BSV_aggregate"]
	for filename in files:
	
		year_dict = years_of_observations(filename)
		year_dict = return_burrow_list(filename, year_dict)
		burrow_occupancy = overall_burrow_occupancy_by_year(filename, year_dict)
		plot_burrow_occupancy(burrow_occupancy, filename, year_dict)
		
