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

def analyze_cohabitation(filename, tort_dict):
	G=nx.Graph()
	G.add_nodes_from(tort_dict.keys())
	plt.clf()
	cursor = db.cursor()
	query = """select Burrow_number, Date, count(Burrow_number) from """ + filename + """ where Burrow_number>"" group by Burrow_number, Date; """
	cursor.execute(query)
	results = cursor.fetchall()
	cohab = [row for row in results if row[2]>1]
	cohab_by_sex=[]
	
	for entry in cohab:
		cursor = db.cursor()
		cursor.execute("""select sex, Tortoise_number, time from """ + filename + """ where Burrow_number = %s and Date=%s; """,(entry[0], entry[1]))
		tort_results = cursor.fetchall()
		#print entry[0], entry[1], tort_results
		# append the sex list of cohabiting torts in a list
		sex_type = sorted([sex[0] if len(sex[0])> 0 else "O" for sex in tort_results])
		sex_type =  "".join(sex_type) # joining the list ["M", "F"] = "MF"
		#calculating n choose 2 for sex_type so that we have only 3 categories
		sex_list=[]
		for pt1 in xrange(len(sex_type)):
			for pt2 in range(pt1, len(sex_type)):
				sex_list.append(sex_type[pt1]+sex_type[pt2])
			
		sex_list= ["MF"  if num=="FM" else num for num in sex_list]
		sex_list= ["FJ"  if num=="JF" else num for num in sex_list]
		sex_list= ["MJ"  if num=="JM" else num for num in sex_list]	
		cohab_by_sex.append(sex_list)
		#change all 'FM' entries to 'MF'
		
		# making a flat list
		
		###########################################
		# to plot cohab network
		#these are the torts the cohabited a burrow
		tort_id = [row[1] for row in tort_results]
		# add edges between all the nodes in the tort_id list
		for i, u in enumerate(tort_id):
			for j in range(i+1, len(tort_id)):
				v = tort_id[j]
				#prevent self loop and double edges
				if u!=v and not G.has_edge(u,v): G.add_edge(u,v)
		###########################################
	
	
	cohab_by_sex = [item for sublist in cohab_by_sex  for item in sublist]
	#print cohab_by_sex	
	

	
	return cohab_by_sex, G
	
######################################################################################
def plot_cohabitation_sexwise_normalize_byedges(filename, cohab_by_sex):
	
	# Count the total male, female and juvenile interaction
	
	total_male_interaction = cohab_by_sex.count('MM') + cohab_by_sex.count('MF') + cohab_by_sex.count('MJ')  
	total_female_interaction = cohab_by_sex.count('FF') + cohab_by_sex.count('MF') + cohab_by_sex.count('FJ') 
	total_juvenile_interaction = cohab_by_sex.count('JJ') + cohab_by_sex.count('MJ') + cohab_by_sex.count('FJ') 
	
	cohab_dict={}
	cohab_dict["MF(male-wise)"] = 0
	cohab_dict["MF(female-wise)"] = 0
	cohab_dict["MJ(male-wise)"] = 0
	cohab_dict["MJ(juvenile-wise)"] = 0
	cohab_dict["FJ(female-wise)"] = 0
	cohab_dict["FJ(juvenile-wise)"] = 0
	cohab_dict["MJ"] = 0
	cohab_dict["FJ"] = 0
	cohab_dict["JJ"] = 0
	cohab_dict["MM"] = 0
	cohab_dict["FF"] = 0
	#counting the total number of "MM", "MF", "FF", "MJ", "
	for x in cohab_by_sex:
		if x == "MM" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_male_interaction)
		if x == "FF" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_female_interaction)
		if x == "JJ" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_juvenile_interaction)
		if x == "MF" :
			cohab_dict["MF(male-wise)"] = cohab_by_sex.count(x)/ (1.0*total_male_interaction)
			cohab_dict["MF(female-wise)"] = cohab_by_sex.count(x)/ (1.0*total_female_interaction)
		
		if x == "MJ" :
			cohab_dict["MJ(male-wise)"] = cohab_by_sex.count(x)/(1.0*total_male_interaction)
			cohab_dict["MJ(juvenile-wise)"] = cohab_by_sex.count(x)/(1.0*total_juvenile_interaction)
			
		if x == "FJ" :
			cohab_dict["FJ(female-wise)"] = cohab_by_sex.count(x)/(1.0*total_female_interaction)
			cohab_dict["FJ(juvenile-wise)"] = cohab_by_sex.count(x)/(1.0*total_juvenile_interaction)
		

	##################################################
	
	# The following commands plots grouped bar plots. x-axis labels = males, females, juveniles
	# for males =  1) #MM interaction/ (#MM + #MF +MJ interactions), 2) #MF interaction/ (#MM + #MF +MJ interactions), 
	#		3) #MJ interaction/ (#MM + #MF +MJ interactions)
	# for females =  1) #MF interaction/ (#FF + #MF +FJ interactions), 2) FF interaction/ (#FF + #MF +FJ interactions), 
	#		3) #FJ interaction/ (#FF + #MF +FJ interactions)
	# for juveniles =  1) #MJ interaction/ (#JJ + #MJ +FJ interactions), 2) # FJ interaction/ (#JJ + #MJ +FJ interactions), 
	#		3) #JJ interaction/ (#JJ + #MJ +FJ interactions)
			
	N = 3
	ind = np.arange(N)  # the x locations for the groups
	width = 0.2      # the width of the bars
	
	male_interaction = (cohab_dict['MM'], cohab_dict["MF(female-wise)"], cohab_dict["MJ(juvenile-wise)"])
	fig, ax = plt.subplots()
	rects1 = ax.bar(ind, male_interaction , width, color='b')
	
	female_interaction = (cohab_dict["MF(male-wise)"], cohab_dict["FF"], cohab_dict["FJ(juvenile-wise)"])
	rects2 = ax.bar(ind+width, female_interaction , width, color='r')
	
	female_interaction = (cohab_dict["MJ(male-wise)"], cohab_dict["FJ(female-wise)"], cohab_dict["JJ"])
	rects3 = ax.bar(ind+width+width, female_interaction , width, color='g')
	
	# add some
	ax.set_ylabel('Mean number of observations')
	ax.set_title('Cohabitation for '+ filename )
	ax.set_xticks(ind+width)
	ax.set_xticklabels( ('Males', 'Females', 'Juveniles') )

	ax.legend( (rects1[0], rects2[0], rects3[0]), ('Males', 'Females', 'Juveniles') )
	plt.show()
	#plt.savefig("cohabitation_by_sex_"+filename+".png")
	##################################################
	
######################################################################################
def plot_cohabitation_sexwise_normalize_bynodes(filename, cohab_by_sex, tort_dict):
	
	# Count the total male, female and juvenile interaction
	
	total_males =  tort_dict.values().count('M')  
	total_females= tort_dict.values().count('F')  
	total_juveniles = tort_dict.values().count('J')  
	
	cohab_dict={}
	cohab_dict["MF(male-wise)"] = 0
	cohab_dict["MF(female-wise)"] = 0
	cohab_dict["MJ(male-wise)"] = 0
	cohab_dict["MJ(juvenile-wise)"] = 0
	cohab_dict["FJ(female-wise)"] = 0
	cohab_dict["FJ(juvenile-wise)"] = 0
	cohab_dict["MJ"] = 0
	cohab_dict["FJ"] = 0
	cohab_dict["JJ"] = 0
	cohab_dict["MM"] = 0
	cohab_dict["FF"] = 0
	#counting the total number of "MM", "MF", "FF", "MJ", "
	for x in cohab_by_sex:
		if x == "MM" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_males)
		if x == "FF" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_females)
		if x == "JJ" :cohab_dict[x] = cohab_by_sex.count(x)/ (1.0*total_juveniles)
		if x == "MF" :
			cohab_dict["MF(male-wise)"] = cohab_by_sex.count(x)/ (1.0*total_males)
			cohab_dict["MF(female-wise)"] = cohab_by_sex.count(x)/ (1.0*total_females)
		
		if x == "MJ" :
			cohab_dict["MJ(male-wise)"] = cohab_by_sex.count(x)/(1.0*total_males)
			cohab_dict["MJ(juvenile-wise)"] = cohab_by_sex.count(x)/(1.0*total_juveniles)
			
		if x == "FJ" :
			cohab_dict["FJ(female-wise)"] = cohab_by_sex.count(x)/(1.0*total_females)
			cohab_dict["FJ(juvenile-wise)"] = cohab_by_sex.count(x)/(1.0*total_juveniles)
		

	##################################################
	
	# The following commands plots grouped bar plots. x-axis labels = males, females, juveniles
	# for males =  1) #MM interaction/ (#male nodes), 2) #MF interaction/ (#male nodes), 
	#		3) #MJ interaction/ (#male nodes)
	# for females =  1) #MF interaction/ (#female nodes), 2) FF interaction/ (#female nodes), 
	#		3) #FJ interaction/ (#female nodes)
	# for juveniles =  1) #MJ interaction/ (#juvenile nodes), 2) # FJ interaction/ (#juvenile nodes), 
	#		3) #JJ interaction/ (#juvenile nodes)
			
	N = 3
	ind = np.arange(N)  # the x locations for the groups
	width = 0.2      # the width of the bars
	
	male_interaction = (cohab_dict['MM'], cohab_dict["MF(female-wise)"], cohab_dict["MJ(juvenile-wise)"])
	fig, ax = plt.subplots()
	rects1 = ax.bar(ind, male_interaction , width, color='b')
	
	female_interaction = (cohab_dict["MF(male-wise)"], cohab_dict["FF"], cohab_dict["FJ(juvenile-wise)"])
	rects2 = ax.bar(ind+width, female_interaction , width, color='r')
	
	female_interaction = (cohab_dict["MJ(male-wise)"], cohab_dict["FJ(female-wise)"], cohab_dict["JJ"])
	rects3 = ax.bar(ind+width+width, female_interaction , width, color='g')
	
	# add some
	ax.set_ylabel('Mean number of observations')
	ax.set_title('Cohabitation (aggregate nodewise) for '+ filename )
	ax.set_xticks(ind+width)
	ax.set_xticklabels( ('Males', 'Females', 'Juveniles') )

	ax.legend( (rects1[0], rects2[0], rects3[0]), ('Males', 'Females', 'Juveniles') )
	#plt.show()
	plt.savefig("cohabitation_sexwise_bynodes_"+filename+".png")
	##################################################
	

###################################################################################
def plot_cohabitation_histogram(filename):
	plt.clf()
	cursor = db.cursor()
	query = """select Burrow_number, Date, count(Burrow_number) from """ + filename + """ where Burrow_number>"" group by Burrow_number, Date; """
	cursor.execute(query)
	results = cursor.fetchall()
	
	cohab = [row[2] for row in results]
	plt.hist(cohab)
	plt.xlabel("Number of tortoise cohabiting a burrow")
	plt.ylabel ("Frequency")
	plt.title (filename)
	plt.savefig("cohabitation_"+filename+".png")

######################################################################################
def list_of_torts(filename):
	# this dict contains key=tort id and and value = sex
	tort_dict = {}
	cursor = db.cursor()
	query = """select Tortoise_number, Sex from """+ filename+""" group by Tortoise_number; """
	cursor.execute(query)
	results = cursor.fetchall()
	for row in results:
		# omit any null tort entries
		if len(row[0])>0:
			#check for missing sex entries and replace those with "O"
			if len(row[1])>0 and row[1]!="?" and row[1]!="*" and row[1]!="U" : tort_dict[row[0]] = row[1] 
			else:  tort_dict[row[0]] = "O"
	
	
	return tort_dict
		
   

#########################################################################################################
def find_average_homerange(G):
	
	#position is the dictionary with key = node, val = array([average easting location, average northing location])
	position = {}
	for node in G.nodes():
		cursor = db.cursor()
		cursor.execute( """select UTM_easting, UTM_northing from """ + filename + """ where Tortoise_number = %s and UTM_easting > 0 and UTM_northing > 0; """, (node))
		results = cursor.fetchall()
		x_avg = np.mean([row[0] for row in results])
		y_avg=  np.mean([row[1] for row in results])
		position[node] = np.array([x_avg, y_avg])
	return position

#########################################################################################################
def draw_cohab_network(G, tort_dict, filename):

	color_key = {"M": "b", "F":"r", "m": "b", "m":"r", "J": "g",  "j": "g",  "O": "k"}
	isolates = [node for node in G.nodes()  if G.degree(node) < 1]
	# removing all the nodes with 0 degree for better visualization
	G.remove_nodes_from(isolates)
	
	nodelist = G.nodes()
	#print ("printing nodelist"), nodelist
	#print ("recheck"), tort_dict.keys()
	#print ("check"), [tort_dict[num] for num in nodelist]
	
	nodecolor = [color_key[tort_dict[num]] for num in nodelist]
	
	#assigning sex attributes to the nodes : for writing graphml
	for node1 in G.nodes():
		print ("node = "), node1, str(tort_dict[node1])
		G.node[node1]["sex"] = tort_dict[node1]
	
	# node position = average home range of the tortoises
	pos = find_average_homerange(G) 
	
	#for node in G.nodes():
	#	print ("node and sex"), filename, node, tort_dict[node]
	nx.draw_networkx_nodes(G, pos, node_list = nodelist, node_color = nodecolor)
	nx.draw_networkx_edges(G, pos)
	nodelabel={}
	for node in G.nodes():
		nodelabel[node] = node
	nx.draw_networkx_labels(G, pos, labels=nodelabel, font_color='Gold', font_size= 8)
	#plt.title("Cohabitation for site = " +filename+ ", node pos= avg home range, color = b:male, f=female, g=juv, k =unknown")
	#plt.show()
	#plt.savefig("Cohab network for "+filename)
	return G

#########################################################################################################
if __name__ == "__main__":
	files = ["BSV_aggregate", "CS_aggregate", "FI_aggregate","HW_aggregate","LM_aggregate", "MC_aggregate", "PV_aggregate", "SG_aggregate", "SL_aggregate"]
	#files = ["BSV_aggregate"]
	for filename in files:
		tort_dict = list_of_torts(filename)
		cohab_by_sex, G = analyze_cohabitation(filename, tort_dict)
		#plot_cohabitation_sexwise_normalize_byedges(filename, cohab_by_sex)
		#plot_cohabitation_sexwise_normalize_bynodes(filename, cohab_by_sex, tort_dict)
		draw_cohab_network(G, tort_dict, filename)
		nx.write_graphml (G, "cohab_network_" + filename+".graphml")
		
######################################################################################

# BSV: update date in observation # 4696 to 1998-03-25

# FI: update date in observation #124201 to 2011-10-26
# FI: update date in observation #124485 to 2011-05-01
# FI: update date in observation # 124195 to 2011-04-30
# FI: DELETE FROM FI_aggregate WHERE observation = 131052; (empty row)


# LM: update LM_aggregate set date = "1999-10-01" where observations = 763;
# PV: Updatesd date format
# SG updated date format
# SG: DELETE FROM SG_aggregate WHERE observation = 1;
# SL updated date format

#############################################################
#updating sex entries

#CS: update CS_aggregate set sex = "M" where observations = 2320 and Tortoise_number = "cs0044";
#CS: update CS_aggregate set sex = "F" where observations = 7109 and Tortoise_number = "Cs0032";

# delete all the nest obervations;
#LM: delete from LM_aggregate where observations = 20 ;
#LM: delete from LM_aggregate where observations = 420 ;

# delete unmarked torts observed in a burrow:
#delete from LM_aggregate where observations = 358;
#delete from LM_aggregate where observations = 763 ;
