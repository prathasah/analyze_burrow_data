import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
import networkx as nx
from networkx.algorithms import bipartite

######################################################################################

# Open database connection
db = sql.connect("localhost","root","bio123456","burrow_data" )
# prepare a cursor object using cursor() method

######################################################################################
def draw_bipartite_network(filename):
	
	B = nx.Graph()
	burr_list, tort_list = return_node_list(filename)
	
	# Adding burrows as bottom nodes
	B.add_nodes_from(burr_list, bipartite = 0)
	# Adding tort as top nodes
	B.add_nodes_from(tort_list, bipartite = 1)
	
	B= add_edges(B, filename, burr_list, tort_list)	
	
	# removing isolates
	isolates = nx.isolates(B)
	B. remove_nodes_from(isolates)
	return B

######################################################################################
def return_node_list(filename):

	###############################
	#extracting burrow_list
	# prepare a cursor object using cursor() method
	cursor = db.cursor()
	query = """ select  burrow_number from """ + filename + """ where burrow_number> "" group by burrow_number;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	burr_list = [row[0] for row in results] 
	#removing whitespace for burrow ids
	burr_list = [burr.replace(" ", "") for burr in burr_list]
	
	
	###############################
	#extracting tortoise list
	# prepare a cursor object using cursor() method
	cursor = db.cursor()
	query = """ select  Tortoise_number from """ + filename + """ where tortoise_number >"" group by Tortoise_number;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	tort_list = [row[0] for row in results] 
	
	# Add the letter"T" to each tort to avoid confusion with burrow-ids
	tort_list = ["T"+str(tort) for tort in tort_list]
	return burr_list, tort_list
	
######################################################################################
def add_edges(B, filename, burr_list, tort_list):

	###############################
	#extracting edges
	# prepare a cursor object using cursor() method
	cursor = db.cursor()
	query = """ select  burrow_number, tortoise_number from """ + filename + """ where burrow_number > "" group by burrow_number, tortoise_number;"""
	# execute SQL query using execute() method.
	cursor.execute(query)
	# Fetch all the rows in a list of lists.
	results = cursor.fetchall()
	
	# connecting edges
	for row in results:
		burr = row[0]
		tort = "T"+str(row[1])
		if B.has_node(burr) and B.has_node(tort): 
			B.add_edge(burr, tort)
			print burr, tort, bipartite.is_bipartite(B)
		elif not B.has_node(burr): ("mising burrow node==="), row[0]
		elif not B.has_node(tort): ("mising tort node==="), row[1]
		
	return B



########################################################################################################3
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	
	
	for filename in files:
		B = draw_bipartite_network(filename)
		nx.write_graphml(B, "bipartite_"+filename+".graphml")
