import girder_client, json, sys, requests 
from extract_classes import *

def rect_to_pts(x, k):
	centerX = float(x["annotation"]["elements"][k]["center"][0])
	centerY = float(x["annotation"]["elements"][k]["center"][1])
	height = float(x["annotation"]["elements"][k]["height"] /2)
	width = float(x["annotation"]["elements"][k]["width"] /2) 
	btmLeft = [centerX-width, centerY-height]
	btmRight = [centerX+width, centerY-height]
	topLeft =  [centerX-width, centerY+height]
	topRight = [centerX+width, centerY+height]
	pts = [btmLeft, btmRight, topRight, topLeft]
	return pts 

def polygon_to_pts(x ,k):
	ptsNum = len(x["annotation"]["elements"][k]["points"])
	pts = []
	for l in range(ptsNum):
		ptsX = float(x["annotation"]["elements"][k]["points"][l][0])
		ptsY = float(x["annotation"]["elements"][k]["points"][l][1])
		ptsPair = [ptsX, ptsY]
		pts.append(ptsPair)
		#print(pts)
	return pts 	

def getFullList(gc): 

	# # Initialize Girder CLient instance 
	# gc = girder_client.GirderClient(apiUrl=url)

	# # Authentication
	# try:
	# 	gc.authenticate(user, password)
	# except requests.ConnectionError:
	# 	sys.exit('Authentication Failed! Your url, username, and password might be wrong.')

	# Get list of annotated images 
	annt_Images = gc.get('annotation/images')

	# Iterate through list and retrieve ID, name and annotations
	itSize = len(annt_Images)
	itemList = []

	try: 
		a1 = gc.get('annotation')
	except:
		sys.exit('fail to get annotations')

	anntSize = len(a1)

	# Iterating through all the annotated slides
	for i in range(itSize):
		
		#initializing an Item
		itemName = annt_Images[i]["name"]
		itemID = annt_Images[i]["_id"]

		img_Str = "item/" + itemID + "/tiles"

		try:
			metadata = gc.get(img_Str)
		except girder_client.HttpError:
			sys.exit('Metadata retrieval failed')

		item = Item(itemName, itemID, metadata["sizeX"], metadata["sizeY"])
		crtList = []

		for x in range(anntSize):
			if a1[x]["itemId"] == itemID:
				crtList.append(x)

		# Iterating though annotations of a slide
		for j in crtList:
			anntID = a1[j]["_id"]
			name = a1[j]["annotation"]["name"]
			description = json.dumps(a1[j]["annotation"]["description"]).replace('"', '') 
			#print("description", description)
			#print(isinstance(description, basestring))	
			
			# Call for the annotation through Girder API
			callStr = 'annotation/' + anntID

			try: 
				a1_detail = gc.get(callStr)
			except: 
				sys.exit('Fail to get annotation detials')
				
			if a1_detail["public"] == True:				
				anntNum = len(a1_detail["annotation"]["elements"])
				
				# Iterating through graphs in a annotation
				for k in range(anntNum):
					type = a1_detail["annotation"]["elements"][k]["type"]
					#print(isinstance(type, basestring))	
					#print("type", type)
					#print("name", name)
					# If the graph is a rectangle
					if type == "rectangle":
						pts = rect_to_pts(a1_detail, k)
						#print("rectangle", description)
						annotation = Annotation(itemName,name,description,anntID,pts)
						#print(annotation.description)
						item.add_annotation(annotation)
			
					# If the graph is a polygon
					elif type == "polyline":
						pts = polygon_to_pts(a1_detail, k)
						#print("polyline", description)
						annotation = Annotation(itemName,name,description,anntID,pts)
						#print(annotation.description)
						item.add_annotation(annotation)

		# List of items
		itemList.append(item)

	return itemList

# Add standalone feature
commandLen = len(sys.argv)

if __name__ == '__main__':
	if commandLen != 4:
		sys.exit('Command Line Argvs Error: { Url, User, Password }')
	else :
		url= sys.argv[1]
		user= sys.argv[2]
		password = sys.argv[3]  
		url = url + '/api/v1'
		getFullList(url, user, password)
		
