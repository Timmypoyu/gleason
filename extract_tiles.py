# This program processes slides, extract ROI, 
# separate them into Block, sift them and save.


from api_annt import getFullList 
import numpy as np
import cv2, sys, girder_client, argparse

def argvToList(x = sys.argv):
	""" Return a Full List of Items """
	# Get commandLine to get full annotation list 
	commandLen = len(x)

	if commandLen > 4:
		sys.exit('Command Line Argvs Error: { Url, User, Password }')
	else :
		url= x[1]
		user= x[2]
		password = x[3]  
		url = url + '/api/v1'

		# Initialize Girder CLient instance 
		gc = girder_client.GirderClient(apiUrl= url)

		# Authentication
		try:
			gc.authenticate(user, password)
		except requests.ConnectionError:
			sys.exit('Authentication Failed! Your url, username, and password might be wrong.')
		
		fullList = getFullList(gc)

	return gc, fullList 

# # Return an Item
# def argvToItem(y=0, x = sys.argv):
# 	""" Return a Item object """
# 	commandLen = len(x)

# 	if commandLen > 4:
# 		sys.exit('Command Line Argvs Error: { Url, User, Password }')
# 	else :
# 		url= x[1]
# 		user= x[2]
# 		password = x[3]  
# 		url = url + '/api/v1'
# 		fullList = getFullList(url, user, password)

# 	return fullList[y]

# annotation is one annotation object  
# Naming: PatientID_slideID_AnnotationLabel_GleasonGrade_ROINumber
def getBlocks(annotation, fileName, num, total2, grade):
	
	parsed_Name = fileName.split("_")
	patientID = parsed_Name[0]
	slideID = parsed_Name[1] 
	count = 1

	# Define points
	pts = np.array(annotation.pts, dtype=np.int32)

	# Define image here
	img = cv2.imread(fileName, 1)
	height = img.shape[0]
	width = img.shape[1]

	# White background 
	mask_bg = 255*np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8)

	# Initialize mask
	mask = np.zeros((img.shape[0], img.shape[1]))

	# Create mask that defines the polygon of points
	cv2.fillConvexPoly(mask, pts, 1)
	mask = mask.astype(np.bool)

	# Create output image (untranslated)
	out = np.zeros_like(mask_bg)
	out[mask] = mask_bg[mask]

	# Convert to greyscale to use in findContours fucntion 
	out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY);

	# Bouding Rectangle of ROI
	# Ret, thresh = cv2.threshold(out, 127, 255, 0)
	im2,contours,hierarchy = cv2.findContours(out, 1, 2)
	cnt = contours[0]
	x,y,w,h = cv2.boundingRect(cnt)

	# Mask the image 
	img_processed = cv2.bitwise_and(img,img,mask = out)

	# Crop bounding rect from out
	img_processed_cropped = img_processed[y:y+h, x:x+w].copy()

	# Blocks of images handling
	img_height = img_processed_cropped.shape[0]
	img_width = img_processed_cropped.shape[1]
	cut_height = 200 #should be 512
	cut_width = 200 #should be 512
	total = cut_height * cut_width	
	tile_list = []

	for i in range(img_height, 0, -cut_height):
			for j in range(img_width, 0, -cut_width):
				if(i-cut_height > 0 and j-cut_width > 0):
					tile = img_processed_cropped[i-cut_height:i, j-cut_width:j].copy()

					#how many percentage is white (if > 20, then discard)
					#convert to grayscale then count nonZero's (b&w)
					gray_tile = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY);
					nonzero = cv2.countNonZero(gray_tile)
					zero = total - nonzero
					ratio = zero * 100 / float(total)
					
					#if ratio < 20, then save the image
					if (ratio < 20):
					 	writeName = patientID + '_' + slideID + '_' + 'A' + str(num) + '-' + str(total2) + '_' + 'G' + str(grade) + '_' + str(count) + '.tif' 
						cv2.imwrite(writeName, tile)
						count += 1


def countGleason(item):
	""" return a list that records each gleason gradings in the index of the annotation """
	g1, g2, g3, g4, g5 = ([] for i in range(5))
	annotationSize = len(item.annotations)
	for x in range(annotationSize):
		if item.annotations[x].description == "G1":
			g1.append(x)
		elif item.annotations[x].description == "G2":
			g2.append(x)
		elif item.annotations[x].description == "G3":
			g3.append(x)
		elif item.annotations[x].description == "G4":
			g4.append(x)
		elif item.annotations[x].description == "G5":
			g5.append(x)
	gleason_grade = [g1, g2 ,g3 ,g4 ,g5]	
	return gleason_grade

#takes in an item 
def main(item):
	gleasonList = countGleason(item)
	# Use Gleason Grade as base, iterate through all annotations to process image
	for i in range(len(gleasonList)):
		len1 = len(gleasonList[i])
		if len1 != 0:
			for j in gleasonList[i]:
			 	count = 1
			 	getBlocks(item.annotations[j], item.name, count, len1, i+1)

# still need to get the item 
if __name__ == '__main__':

	# parser = argparser.ArgumentParser()
	# parser.add_argument("url", help="Url on which girder runs", type=str)
	# parser.add_argument("username", help="Username (\"admin\") ", type=str)
	# parser.add_argument("password", help="Password (\"password\")", type=str)
	# parser.add_argument("-n", "--name", help="Name of the large image of interest", type=str)
	# parser.add_argument("-hema", "--hematoxylin", help = "Output hematoxylin channel exclusively", action="store_true")
	# args = parser.parse_args()


	argvLen = len(sys.argv)
	if argvLen == 4:
		gc, listAll = argvToList()
		itemNum = len(listAll)
		for i in range(itemNum):
			main(listAll[i])
	elif argvLen == 5:
		gc, listAll = argvToList()
		itemNum = len(listAll)
		count = 0 
		for i in range(itemNum):
			if listAll[i].itemID == sys.argv[4]:
				main(listAll[i])
				count += 1
		if count == 0:
			print("The image you specified is not annotated")
	else:
		print("Command Line Arguments are incorrect")




