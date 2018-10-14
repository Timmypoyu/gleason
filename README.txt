Thie program sought out to extract regions of interest (ROI) from an annotated slide image and then further processed them into smaller, square blocks of images. It is consisted of three python script files:

(1) extract_classes.py : doucment python class objects of (1)Item and (2)Annotation, with each of their own metadatas (such as name, ID, desciption, coordinates). In an item object, there is a list of its annotations, and in a annotation object, there is a list of the annotations' coordinates.

(2) annt_api.py : handling api calls to get annotations, and coordinates, in order to initialize objects of Items and Annotations to create a list of Items to be fed into extract_tiles.py . 
annotations to coordinates. 

(3) extract_tiles.py: In extract_tiles, an images annotations are used to extract the ROI and then divided into square blocks. This script also handles the naming scheme of the square blocks iamges. 

To use this program, one needs to run extract_tiles.py with the commandline of the apiURL, Username and password. For example: 

> python extract_tiles.py http://localhost:8080 admin password

There are still a few features to be added: 
(1) using a filename to specify which slide images to be processed. (As currently, the selection of the image is being done internally)

(2) Iterating through all annootations and Items to get the entire reservoir of ROI's