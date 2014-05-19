import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
from datetime import datetime
from datetime import timedelta
import networkx as nx
from pylab import *

######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method


######################################################################################
def overall_burrow_occupancy_by_year(filename, year_dict):

	cursor = db.cursor()
	query = """select Tortoise_number, Burrow_number, year(Date), count(Tortoise_number) from """ +filename+ """ where Burrow_number>"" and Tortoise_number>"" group by Tortoise_number, Burrow_number, year(Date); """
	cursor.execute(query)
	results = cursor.fetchall()
	
	for row in results:
		#year_dict[year][tortoise number] = [list of burrows that the tort visited (including repeats)]
		#print row[0], str(row[2])
		year_dict[str(row[2])][row[0].upper()].append(row[1]) 
		
	#removing repeat of burrow visitation and counting the number of animals that visited the burrow in the particular year
	burrow_occupancy= {}
	for year in year_dict.keys():
		burrow_occupancy[year] = []
		for tort in year_dict[year].keys():
			#count the number of unique torts that visited the burrow in a particular year
			burrow_occupancy[year].append(len(set(year_dict[year][tort])))
	
	return burrow_occupancy

######################################################################################
def sexwise_overall_burrow_occupancy_by_year(filename, sex_dict):

	cursor = db.cursor()
	query = """select sex, Burrow_number, year(Date), count(sex) from """ +filename+ """ where Burrow_number>"" and sex>"" group by sex, Burrow_number, year(Date); """
	cursor.execute(query)
	results = cursor.fetchall()
	
	for row in results:
		#sex_dict[sex][year] = [list of burrows that the torts of paritcular sex visited (including repeats)]
		#print row[0], str(row[2])
		sex_dict[row[0].upper()][str(row[2])].append(row[1]) 
		
	#removing repeat of burrow visitation and counting the number of animals that visited the burrow in the particular year
	burrow_occupancy= {}
	for sex in sex_dict.keys():
		burrow_occupancy[sex] = []
		for year in sex_dict[sex].keys():
			#count the number of unique burrows that torts of a particular sex visited over the years 
			burrow_occupancy[sex].append(len(set(sex_dict[sex][year])))
	
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
def return_tortoise_list(filename, year_dict):
	"""returns the dict of burrows for each year of observation"""
	
	cursor = db.cursor()
	query = """select Tortoise_number from """ +filename+ """ where Tortoise_number>"" group by Tortoise_number;"""
	cursor.execute(query)
	results = cursor.fetchall()

	#converting all the names into upper case
	tort_list = [row[0].upper() for row in results]
	print tort_list
	for year in year_dict.keys():
		for tort in tort_list:
			year_dict[year][tort]=[]
	return year_dict

######################################################################################
def return_sex_list(filename):
	"""returns the dict of burrows for each year of observation"""
	
	cursor = db.cursor()
	query = """select sex from """ +filename+ """ where sex>"" and sex!="?" group by sex;"""
	cursor.execute(query)
	results = cursor.fetchall()

	#converting all the names into upper case
	sex_list = [row[0].upper() for row in results]
	sex_dict={}
	for sex in sex_list:
		sex_dict[sex]={}
		
	
	cursor = db.cursor()
	query = """select year(date) from """ +filename+ """ group by year(date);"""
	cursor.execute(query)
	results = cursor.fetchall()
	
	year_list = [str(row[0]) for row in results]
	
	for sex in sex_dict.keys():
		for year in year_list:
			sex_dict[sex][year] = []
	return sex_dict
		
	
	

	
######################################################################################
def plot_burrow_occupancy(burrow_occupancy, filename):
	
	bin_list = [x for x in xrange(20)]
	occupancy_list = []
	count = 0
	plt.clf()
	for year in burrow_occupancy.keys():
		occupancy = burrow_occupancy[year]
		print occupancy
		counts, bin_edges  = np.histogram(occupancy, bins = bin_list)
		
		occupancy_list.append(list(counts))
		count+=1
		
	
	ylist = [np.mean(num) for num in zip(*occupancy_list)]
	err_list = [np.std(num) for num in zip(*occupancy_list)]
	print bin_list, ylist
	print len(bin_list), len(ylist)
	xaxis = [x for x in xrange(19)]
	plt.bar(xaxis, ylist, yerr = err_list, ecolor = "k", align = "center")
	plt.title ("Avg # burrows visited by tortoises in a year, Site = " + filename)
	plt.xlabel("Number of burrows visited")
	plt.ylabel ("Frequency")
	plt.xlim([-1, 20])
	plt.savefig("Burrow_used_by_torts_peryear_"+filename)
	#plt.show()

######################################################################################
def plot_sexwise_burrow_usage(burrow_occupancy, filename):
	
	print burrow_occupancy
	plt.clf()
	ylist = [np.mean(burrow_occupancy[sex]) for sex in burrow_occupancy.keys()]
	err_list =[np.std(burrow_occupancy[sex]) for sex in burrow_occupancy.keys()]
	xaxis =  [x for x in xrange(len(burrow_occupancy.keys()))]
	
	plt.bar(xaxis, ylist, yerr = err_list, ecolor = "k", align = "center")
	plt.title ("Avg # burrows visited by tortoises (sexwise) in a year, Site = " + filename)
	plt.xticks(xaxis,  burrow_occupancy.keys())
	plt.xlabel("Number of burrows visited")
	plt.ylabel ("Frequency")
	plt.savefig("Burrow_used_sexwise_peryear_"+filename)

#########################################################################################################
if __name__ == "__main__":
	#files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	files = ["BSV_aggregate", "CS_aggregate", "HW_aggregate","LM_aggregate", "MC_aggregate", "SL_aggregate"]
	for filename in files:
			
		#### plot overall burrow usage by torts
		#year_dict = years_of_observations(filename)
		#year_dict = return_tortoise_list(filename, year_dict)
		#burrow_occupancy = overall_burrow_occupancy_by_year(filename, year_dict)
		#plot_burrow_occupancy(burrow_occupancy, filename)
		
		#### plot overall burrow usage by sex
		sex_dict = return_sex_list(filename)
		burrow_occupancy = sexwise_overall_burrow_occupancy_by_year(filename, sex_dict)
		plot_sexwise_burrow_usage(burrow_occupancy, filename)
		
		
