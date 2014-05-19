import matplotlib.pyplot as plt
import MySQLdb as sql
import numpy as np
from datetime import datetime
from datetime import timedelta
import networkx as nx
import utm
######################################################################################

# Open database connection
db = sql.connect(host = "localhost", user = "root", passwd = "bio123456", db ="burrow_data")
# prepare a cursor object using cursor() method

######################################################################################
def create_burrow_network(filename, burr_dict):
	
	G=nx.Graph()
	G.add_nodes_from(burr_dict.keys())
	G = add_node_attribute(G, burr_dict)
	
	for burr in burr_dict.keys():
		cursor = db.cursor()
		cursor.execute("""select Tortoise_number, Date from """+ filename+""" where Burrow_number = %s; """, (burr))
		results = cursor.fetchall()
		for row in results:
			tort = row[0]
			date_visit = row[1]
			#print ("burrow, tort and date = "), burr, row[0], row[1]
			# search for all the burrows that tort visited within this particular week
			cursor = db.cursor()
			cursor.execute("""select Burrow_number from """+ filename+""" where Tortoise_number = %s and Burrow_number>"" and Burrow_number != %s and  weekofyear(date) = weekofyear(%s) and year(date) = year(%s)""", (tort, burr, date_visit, date_visit))
			
			results1 = cursor.fetchall()
			#retrieve all the burrows that the tort visited within this particular week of the year 
			burrow_list = [row[0] for row in results1]
			
			#connect edges but avoid self-loop
			if len(burrow_list)>0:
				#print ("connecting to...."), burrow_list
				[G.add_edge(burr, burr1) for burr1 in burrow_list if burr!=burr1]
	
	return G
		

######################################################################################
def add_node_attribute(G, burr_dict):

	for node in G.nodes():
		if burr_dict[node][0] > 0 and  burr_dict[node][1] >0:
			latitude, longitude = utm.to_latlon(burr_dict[node][0], burr_dict[node][1], 11, northern = True)
			G.node[node]["Latitude"] = latitude
			G.node[node]["Longitude"] = longitude
		else: print ("node with missing location"), node
	return G

######################################################################################

def  plot_burrow_network(G, burr_dict, filename):
	
	nodelist = G.nodes()
	pos = nx.spring_layout(G,  iterations=15, scale = 3)
	nx.draw_networkx_nodes(G, pos, node_list = nodelist)
	nx.draw_networkx_edges(G, pos)
	nodelabel={}
	print ("network generated!, edges are"), G.edges()
	for node in G.nodes():
		nodelabel[node] = node
	nx.draw_networkx_labels(G, pos, labels=nodelabel, font_color='Gold', font_size= 8)
	plt.title("Burrow use network for site = " +filename)
	plt.show()

######################################################################################

def create_burrow_dict(filename):	
	
	cursor = db.cursor()
	query = """select Burrow_number, UTM_Easting, UTM_Northing from """+ filename+""" where Burrow_number> "" group by Burrow_number ; """
	cursor.execute(query)
	results = cursor.fetchall()
	burr_dict = {}
	for row in results:
		# omit any null burr entries
		if len(row[0])>0:
			# burr_dict contains val = [UTM_easting, UTM_northing]
			burr_dict[row[0]] = (row[1], row[2]) 
		
	return burr_dict

#########################################################################################################

if __name__ == "__main__":
	#files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "SG_aggregate", "SL_aggregate"]
	for filename in files:
		# call function for creating a burrow list with keys= burrow_id and value = [easting, northing]
		burr_dict = create_burrow_dict(filename)
		# call function for creating a network where nodes = burrows and edges = tort that visiting both the burrow within the same week
		G = create_burrow_network(filename, burr_dict)
		isolates = [node for node in G.nodes()  if G.degree(node) < 1]
		G.remove_nodes_from(isolates)
		nx.write_graphml(G, "burrow_network_"+filename+".graphml")
		# call function for plotting the network
		#plot_burrow_network(G, burr_dict, filename)
