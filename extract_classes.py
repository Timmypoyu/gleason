class Item:

    # Constructor 
    def __init__(self, name, itemID, sizeX, sizeY, annotations=None):
        self.name = name
        self.itemID = itemID
        # List of annotations 
        self.annotations = annotations if annotations is not None else []
        self.sizeX = sizeX
        self.sizeY = sizeY


    # Appendding an annotation 
    def add_annotation(self, annotation):
        self.annotations.append(annotation)

def make_item(name, itemID):
    item = Item(name, itemID)
    return item

class Annotation:

    # Constructor 
    # pts is a list that contains coordinates 
    def __init__(self, itemName, name, description, anntID, pts=None):
        self.itemName = itemName
        self.name = name
        self.description = description
        self.anntID = anntID
        self.pts = pts if pts is not None else []

    def init_pts(self, pts):
        if pts != None:
            self.pts = pts 

