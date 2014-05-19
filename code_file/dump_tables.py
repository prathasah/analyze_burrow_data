import csv
import MySQLdb as sql

filename = "SG_aggregate"

######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method

######################################################################################
cursor = db.cursor()
query = """select * from """ + filename + """ ;"""
cursor.execute(query)
results = cursor.fetchall()


data =[]
heading = ["obervations", "tortoise_number", "data", "time", "sex", "location", "burrow_number", "UTM_easting", "UTM_northing", "Air temperature", "behavior", "tort condition", "elevation", "habitat", "julian", "notes", "plot", "radio", "radio frequency", "soil", "weather"]
data.append((heading))
for row in results:
	print row[0]
	data.append((row))


with open (filename +".csv", "w") as f1:
		a = csv.writer(f1, delimiter=',')
		
		
		a.writerows(data)
