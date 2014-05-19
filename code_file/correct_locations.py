import MySQLdb as sql
import numpy as np
import collections as cl
######################################################################################
#####This script corrects the easting and northing location of burrow. It also deals###########
###### with missing location when there is enough data to fill in the coordinates#############################

######################################################################################

# Open database connection
db = sql.connect("localhost","root","bio123456","burrow_data" )
# prepare a cursor object using cursor() method

########################################################################################################3
def check_burrow_location_consistency(filename):

	# prepare a cursor object using cursor() method
	cursor = db.cursor()
	query = """ select UTM_Easting, UTM_Northing, burrow_number from """ + filename + """ where burrow_number >"" and UTM_Easting > "" and UTM_northing> "";"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	# create a dictionay called burr and store all the easting nd northing location as tuple
	burr={}
	for row in results:
		#remove whitespace from the burrow_number string
		burrow= row[2].replace(" ", "")
		#burr(burrow id) = tuple of (easting, northing) i.e. (xcoord, ycoord)
		if burr.has_key(burrow): burr[burrow].append((row[0], row[1])) 
		else: burr[burrow] = [(row[0], row[1])]
	
	# bur_final is a dict with key= val and [northing, easting] as location
	burr_final={}
	for burrow in burr.keys():
		# add key to the final dict
		burr_final[burrow]={}
		#Easting is the x-axis coordinates
		easting = [num[0] for num in burr[burrow]]
		#Northing is the y-axis coordinates
		northing = [num[1] for num in burr[burrow]]
		
		ecounter= cl.Counter(easting)
		ncounter= cl.Counter(northing)
		
		# if the most frequenct northing location occurs more than 1, accept that coordinate to be correct:
		if ncounter.most_common()[0][1]>1: burr_final[burrow]['n'] =  ncounter.most_common()[0][0]
		# if the most frequenct northing location occurs more than 1, accept that coordinate to be correct:
		if ecounter.most_common()[0][1]>1: burr_final[burrow]['e'] =  ecounter.most_common()[0][0]
		
		# if both the coordinates have been selected by the above step, then move on to the next burrow
		if  burr_final[burrow].has_key('n') and burr_final[burrow].has_key('e'): 
			continue
		#if not, then approximate the coordinate by first removing outliers and then taking an average
		if not  burr_final[burrow].has_key('n'): 
			burr_final[burrow]['n'] = choose_approx_location(northing)
		if not  burr_final[burrow].has_key('e'): 
			burr_final[burrow]['e'] = choose_approx_location(easting)
	
	return burr_final


###########################################################################################

def choose_approx_location(location_list):
	"""Chooses an approximate value of the burrow location by first removing the ooutliers and then taking an average of 
	the remaining locations"""
	
	avg = np.mean(location_list)
	std = np.std(location_list)
	
	for num in location_list: 
		# remove outliers
		if (num -avg) > 0.3* std: location_list.remove(num)
	return int(np.mean(location_list))
	

###########################################################################################

def update_burrow_locations(filename, burr_final):
	
	""" update the burrow locations"""
	
	for burr in burr_final.keys():
		db = sql.connect("localhost","root","bio123456","burrow_data" )
		# prepare a cursor object using cursor() method
		cursor = db.cursor()
		cursor.execute( """ UPDATE """ + filename + """ SET UTM_Northing= %s, 
		UTM_Easting=%s WHERE Burrow_number=%s""",((burr_final[burr]['n']), (burr_final[burr]['e']),(burr)))
		db.commit()
		db.close()
		

###########################################################################################		
def remove_whitespace(filename):
	cursor = db.cursor()
	#remove whitespce from burrow ids
	cursor.execute("""UPDATE """ + filename + """ SET Burrow_number = REPLACE( Burrow_number, ' ' , '' )""")


###########################################################################################	

if __name__ == "__main__":
# This is the main function, where all the tasks get created

	#files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	files = ["SG_aggregate"]

	for filename in files:
		#connect to the database
		db = sql.connect("localhost","root","bio123456","burrow_data" )
		# Step 1: Remove white spaces from burrow ids
		remove_whitespace(filename)
		# Step 2: Create a dictionary with key=burrow id and value =correct location data
		burr_final = check_burrow_location_consistency(filename)
		db.close()
		####Final Cheack#####
		for burr in burr_final.keys():
			print ("burrow, easting, northing"), filename, burr,burr_final[burr]['e'], burr_final[burr]['n']
		# Step 3: Update database
		update_burrow_locations(filename, burr_final)
	



# Show the entries in location column and their count
#select location, count(*) from BSV_aggregate group by location;

# select easting and northing location when the location is 
# select UTM_Easting, UTM_Northing, location from BSV_aggregate where location = "burrow" or location = "pallet";

