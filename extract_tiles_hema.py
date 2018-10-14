from PIL import Image 
from io import BytesIO
from api_annt import getFullList 
from extract_tiles import *
import numpy as np
import cv2, sys, girder_client, requests 
from extract_tiles_remote import findImageMoment

def getBlocksHema(annotation, item, num, total2, grade, gc):
	"""get Blocks of image of exclusively Hematoxilyn channel"""

	# Get FileID through itemID
	getStr = "item/" + item.itemID + "/files"
	fileID_json = gc.get(getStr)
	fileID = fileID_json[0]["_id"]

	# perform Color disconvolution
	stainName = item.name + "_" + "stain"

	# folder of poyuwu
	folderID = '5afd922f92ca9a048d46ccd5'
	getStr_color = "HistomicsTK/dsarchive_histomicstk_latest/ColorDeconvolution/run" 
	colorJson = gc.post(getStr_color, {'inputImageFile_girderFileId': fileID, 'outputStainImageFile_1_girderFolderId': folderID , 'outputStainImageFile_1_name': stainName + '1.tif' , 'outputStainImageFile_2_girderFolderId': folderID , 'outputStainImageFile_2_name': stainName + '2.tif' , 'outputStainImageFile_3_girderFolderId': folderID, 'outputStainImageFile_3_name': stainName + '3.tif' })

	getStr_item = 'item'
	item1Json = gc.get(getStr_item, {'folderId': folderID, 'name': stainName + '1.tif'})
	item2Json = gc.get(getStr_item, {'folderId': folderID, 'name': stainName + '2.tif'})
	item3Json = gc.get(getStr_item, {'folderId': folderID, 'name': stainName + '3.tif'})
	stain1ID = item1Json[0]["_id"]
	stain2ID = item2Json[0]["_id"]
	stain3ID = item3Json[0]["_id"]

		# Parsing name 
	parsed_Name = item.name.split("_")
	patientID = parsed_Name[0]
	slideID = parsed_Name[1] 
	count = 1

	cnt = findImageMoment(annotation.pts, item)
	x,y,w,h = cv2.boundingRect(cnt)

	# call region and convert to numpy array type
	imgStr = "item/" + stain1ID + "/tiles/region"
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

def main(item, gc):
	gleasonList = countGleason(item)
	# Use Gleason Grade as base, iterate through all annotations to process image
	for grade in range(len(gleasonList)):
		len1 = len(gleasonList[grade])
		if len1 != 0:
			for j in gleasonList[grade]:
			 	count = 1
			 	getBlocksHema(item.annotations[j], item, count, len1, grade+1, gc)

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



