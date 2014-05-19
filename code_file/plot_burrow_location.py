import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np

######################################################################################

# Open database connection
db = sql.connect("localhost","root","bio123456","burrow_data" )
# prepare a cursor object using cursor() method

######################################################################################
def check_outliers(burr, llist):
	avg = np.mean(llist)
	std = np.std(llist)
	
	for num in xrange(len(llist)): 
		# remove outliers
		if (llist[num] -avg) > 0.9* std: print ("check location of burrow"),burr[num], llist[num]

######################################################################################
def plot_burrow_locations(filename, color):

	cursor = db.cursor()
	query = """ select UTM_Easting, UTM_Northing, burrow_number from """ + filename + """ where burrow_number >"" and UTM_Easting >500 and UTM_Northing > 5000;"""
	cursor.execute(query)
	burrow=[]
	northing=[]
	easting =[]
	results = cursor.fetchall()
	count=0
	for row in results:
		burrow.append(row[2])
		northing.append(int(row[1]))
		count+=1
		easting.append(int(row[0]))

		
	plt.scatter(easting, northing, c= color, s=200, alpha=0.4, label = "Burrow locations")
	
		
######################################################################################
def plot_tort_locations(filename, color):
	cursor = db.cursor()
	query = """ select UTM_Easting, UTM_Northing from """ + filename + """ where UTM_Easting > 150000 and UTM_Northing >3820000 and UTM_Easting < 800000 and UTM_Northing < 6000000 ;"""
	#UTM_Easting >400000 and UTM_Northing >3900000 and UTM_Northing  <5000000  ;"""
	cursor.execute(query)
	northing=[]
	easting =[]
	results = cursor.fetchall()
	count=0
	print len(results)
	for row in results:
		easting.append(int(row[0]))
		northing.append(int(row[1]))
		count+=1

		
	plt.scatter(easting, northing, c= color, marker = "D", label = "Tortoise locations")



########################################################################################################3
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]

	colors = ['Black', 'Red', 'Blue', 'DarkGreen', 'DarkMagenta', 'DarkViolet', 'DimGray','Gold','LightCoral']

	mylist = [num for num in xrange(9)]
	for num in mylist:
		#plt.clf()
		filename = files[num]
		color = colors[num] 
		plot_burrow_locations(filename, color)
		plot_tort_locations(filename, color)
		plt.title("Location = "+filename)
		#plt.legend()
	plt.show()
		
	db.close()
######################################################################################
##Outliers detected:
##BSV: burrow 2-530, UTM_Northing change from 39780699 --> 3980699 (extra digit)
## BSV: burrow 1-356, UTM_easting change from 434278  --> 651081 (error in calculating average approx location)
## BSV: burrow 2-697, UTM_Northing change from 390857 --> 3980864 (error in calculating average approx location)


## FI: burrow 1856, UTM _easting change from  256598-->513199 and UTM_northing form 1943369 --> 3886742 (error in calculating average approx location)

## LM: burrow LM-262, UTM _easting change from  368451--> 736902 and UTM_northing form  2020534--> 4041052 (error in calculating average approx location)
## LM: burrow LM-349, UTM _easting change from 368498 --> 736993 and UTM_northing form  2020516--> 4041018  (error in calculating average approx location)


#######################################################################################
