from PIL import Image 
from io import BytesIO
from api_annt import getFullList 
from extract_tiles import *
import numpy as np
import cv2, sys, girder_client, requests 
# from extract_tiles_hema import getBlocksHema 

def findImageMoment(coordList, item):
	# Define points
	pts_origin = np.array(coordList, dtype=np.int32)

	# Define image here
	height = item.sizeX
	width = item.sizeY

	# White background 
	mask_bg = 255*np.ones((height, width, 3), dtype=np.uint8)

	# Initialize mask
	mask = np.zeros((height, width))

	# Create mask that defines the polygon of points
	cv2.fillConvexPoly(mask, pts_origin, 1)
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

	return cnt


def getBlockRemote(annotation, item, num, total2, grade, gc):
	
	# # Initialize Girder CLient instance 
	# url = url + '/api/v1'
	# gc = girder_client.GirderClient(apiUrl=url)

	# # Authentication
	# try:
	# 	gc.authenticate(user, password)
	# except requests.ConnectionError:
	# 	sys.exit('Authentication Failed! Your url, username, and password might be wrong.')

	# Parsing name 
	parsed_Name = item.name.split("_")
	patientID = parsed_Name[0]
	slideID = parsed_Name[1] 
	count = 1

	cnt = findImageMoment(annotation.pts, item)
	x,y,w,h = cv2.boundingRect(cnt)

	# call region and convert to numpy array type
	imgStr = "item/" + item.itemID + "/tiles/region"
	img = gc.get(imgStr, {'left':x, 'top':y, 'right': x+w, 'bottom': y+h, 'encoding':'TIFF', 'tiffCompression':'raw'}, jsonResp=False)
	img = Image.open(BytesIO(img.content))
	pix = np.array(img)
	pix = cv2.cvtColor(pix, cv2.COLOR_BGR2RGB)
	regHeight = pix.shape[0]
	regWidth = pix.shape[1]

	regPts = []
	#all annotation points need to trim by decreasing x and y from each coordinates
	for i in range(len(annotation.pts)):
		# print("x", x)
		# print("y", y)
		# # print(annotation.pts[i][0])
		# print(annotation.pts[i][1])
		x2 = annotation.pts[i][0] - x 
		y2 = annotation.pts[i][1] - y
		regCoord = [x2, y2]
		# print(regCoord)
		regPts.append(regCoord)

	pts = np.array(regPts, dtype=np.int32)
	# White background 
	mask_bg_reg = 255*np.ones((pix.shape[0], pix.shape[1], 3), dtype=np.uint8)

	# Initialize mask
	mask_reg = np.zeros((pix.shape[0], pix.shape[1]))

	# Create mask that defines the polygon of points
	cv2.fillConvexPoly(mask_reg, pts, 1)
	mask_reg = mask_reg.astype(np.bool)

	# Create output image (untranslated)
	out_reg = np.zeros_like(mask_bg_reg)
	out_reg[mask_reg] = mask_bg_reg[mask_reg]


	# Convert to greyscale to use in findContours fucntion 
	out_reg = cv2.cvtColor(out_reg, cv2.COLOR_BGR2GRAY);
	# Mask the image 
	img_processed = cv2.bitwise_and(pix,pix,mask = out_reg)

	# Blocks of images handling
	img_height = img_processed.shape[0]
	img_width = img_processed.shape[1]
	cut_height = 200 #should be 512
	cut_width = 200 #should be 512
	total = cut_height * cut_width	


	for i in range(img_height, 0, -cut_height):
			for j in range(img_width, 0, -cut_width):
				if(i-cut_height > 0 and j-cut_width > 0):
					tile = img_processed[i-cut_height:i, j-cut_width:j].copy()

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

#takes in an item 
def main(item, gc):
	gleasonList = countGleason(item)
	# Use Gleason Grade as base, iterate through all annotations to process image
	for grade in range(len(gleasonList)):
		len1 = len(gleasonList[grade])
		if len1 != 0:
			for j in gleasonList[grade]:
			 	count = 1
			 	getBlockRemote(item.annotations[j], item, count, len1, grade+1, gc)

if __name__ == '__main__':
	argvLen = len(sys.argv)
	if argvLen == 4:

		gc, listAll = argvToList()
		itemNum = len(listAll)
		for i in range(itemNum):
			main(listAll[i], gc)
	elif argvLen == 5:

		gc, listAll = argvToList()
		itemNum = len(listAll)
		count = 0 
		for i in range(itemNum):
			if listAll[i].itemID == sys.argv[4]:
				main(listAll[i], gc)
				count += 1
		if count == 0:
			print("The image you specified is not recorded")
	else:
		print("Command Line Arguments are incorrect")



