### THIS MODULE RENDERS THE TEMPLATES FROM THE JINJA2 FILES
### AND PACKAGES THEM INTO A LIST OF LISTS. IT ONLY LOOKS AT THE 
### SELECTED INDEXES (INIITIALIZE.ELEMENT) OF THE NODE_OBJECT. 
### THE CONFIGURATIONS ARE STORED IN THE GLOBAL VARIABLE CALL 
### INITIALIZE.CONFIGURATION.

from jinja2 import Environment, FileSystemLoader
from multithread import multithread_engine
from directory import get_directory
import re
import initialize

def render_audit(template,node_object):

	controller = 'get_config'
	command = ''

	### INDEX_POSITION IS THE INDEX OF ALL THE MATCHED FILTER_CONFIG AGAINST THE BACKUP_CONFIGS. THE INDEX IS COMING FROM THE BACKUP_CONFIG
	index_position = 0

	### INDEX_LIST IS A LIST OF ALL THE POSITIONS COLLECTED FROM INDEX_POSITION VARIABLE
	index_list = []

	### AUDIT_FILTER_RE IS THE REGULAR EXPRESSION TO FILTER OUT THE AUDIT FILTER IN EVERY TEMPLATE
	AUDIT_FILTER_RE = r"\[.*\]"

	### FILTER_CONFIG IS A LIST OF COLLECTION OF ALL THE AUDIT FILTERS THAT MATCHED THE LINES IN BACKUP_CONFIG. THESE ENTRIES DO NOT CONTAIN DEPTHS/DEEP CONFIGS
	filter_config = []

	### FILTERED_BACKUP_CONFIG IS THE FINAL LIST OF ALL THE AUDIT FILTERS THAT MATCHES THE LINES IN BACKUP_CONFIG. THESE ENTRIES INCLUDE DEPTHS/DEEP CONFIGS
	filtered_backup_config = []
	print("[+] [GATHERING RUNNING-CONFIG. STANDBY...]")
	multithread_engine(initialize.ntw_device,controller,command)
	print("[!] [DONE]")

	for index in initialize.element:
		directory = get_directory(node_object[index]['platform'],node_object[index]['os'],node_object[index]['type'])
		env = Environment(loader=FileSystemLoader("{}".format(directory)))
		baseline = env.get_template(template)
		f = open("/rendered-configs/{}".format(node_object[index]['hostname']) + ".conf", "w") 

		### GENERATING TEMPLATE BASED ON NODE OBJECT
		config = baseline.render(nodes = node_object[index])

		print ("[{}".format(node_object[index]['hostname']) + "#]")
		f.write(config) 
		f.close 
#		print("{}".format(config))
#		print("")

		### OPEN RENDERED CONFIG FILE AND STORE IN RENDERED_CONFIG AS A LIST
		f = open("/rendered-configs/{}".format(node_object[index]['hostname']) + ".conf", "r")
		init_config = f.readlines()
		rendered_config = []

		for config_line in init_config:
			strip_config = config_line.strip('\n')
			if(strip_config == '' or strip_config == "!"):
				continue	
			else:
				rendered_config.append(strip_config)	

#		print ("RENDERED CONFIG: {}".format(rendered_config))
		
		### OPEN BACKUP CONFIG FILE AND STORE IN BACKUP_CONFIG AS A LIST
		f = open("/backup-configs/{}".format(node_object[index]['hostname']) + ".conf", "r")
		init_config = f.readlines()
		backup_config = []

		for config_line in init_config:
			strip_config = config_line.strip('\n')
			backup_config.append(strip_config)	

#		print ("BACKUP CONFIG: {}".format(backup_config))
		
		### THIS WILL OPEN THE JINJA2 TEMPLATE AND PARSE OUT THE AUDIT_FILTER SECTION VIA REGULAR EXPRESSION
		directory = get_directory(node_object[index]['platform'],node_object[index]['os'],node_object[index]['type'])
		f = open("{}".format(directory) + template, "r")
		parse_audit = f.readline()
		audit_filter = eval(re.findall(AUDIT_FILTER_RE, parse_audit)[0])

		### FILTER OUT THE BACKUP_CONFIGS WITH THE AUDIT_FILTER
		for audit in audit_filter:
			query = re.compile(audit)
			filters = list(filter(query.match,backup_config))

			for aud_filter in filters:
				filter_config.append(aud_filter)

#		print("THIS IS THE FILTER_CONFIG: {}".format(filter_config))

		### GETTING THE INDEXES OF FILTER_CONFIG FROM BACKUP_CONFIG
		for config in filter_config:
			if(config in backup_config):
				index_position = backup_config.index(config)
				index_list.append(index_position)
#			print("{}".format(index_list))

		### EXTRACTING ALL RELAVENT CONFIGS PERTAINING TO THE ONES THAT WERE PICKED UP THROUGH FILTERING
		for index_pos in index_list:

			next_element = index_pos + 1

			filtered_backup_config.append(backup_config[index_pos])
			whitespace = (len(backup_config[next_element])-len(backup_config[next_element].lstrip()))
#			print("{}".format(backup_config[index_pos]))
			while(whitespace != 0):
				filtered_backup_config.append(backup_config[next_element])
#				print("{}".format(backup_config[next_element]))
				next_element = next_element + 1
				whitespace = (len(backup_config[next_element])-len(backup_config[next_element].lstrip()))
			

#		print("THIS IS THE FILTERED BACKUP CONFIG: {}".format(filtered_backup_config))		
				
		### COMPARING EACH ELEMENT IN RENDERED_CONFIG AGAINST FILTERED_BACKUP_CONFIG(RUNNING CONFIG OF DEVICE)
		minus_commands = list(set(filtered_backup_config) - set(rendered_config))
		plus_commands = list(set(rendered_config) - set(filtered_backup_config))

#		print("THIS IS MINUS_COMMANDS: {}".format(minus_commands))
		print("")
#		print("THIS IS PLUS_COMMANDS: {}".format(plus_commands))


		if(len(minus_commands) == 0 and len(plus_commands) == 0):
			print("{}{} (none)".format(directory,template))
		else:
			for minus in minus_commands:
				print("- {}".format(minus))
				for anchor in index_list:
					initialize.configuration.append("no {}".format(anchor))
					
			for plus in plus_commands:
				print("+ {}".format(plus))
	
		del rendered_config[:]		
	 	del backup_config[:]
		del index_list[:]
		del filter_config[:]
		del filtered_backup_config[:]

	return None
