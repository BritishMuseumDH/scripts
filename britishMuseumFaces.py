from SPARQLWrapper import SPARQLWrapper, JSON
import urllib
import os
from PIL import Image
import subprocess
import cv2
import stat

# Change this to your script path
basePath = '/Users/danielpett/githubProjects/scripts'
# You will need to download the opencv file haarcascade_frontalface_default.xml for the facial bit to work

if not os.path.exists(os.path.join(basePath, 'bmimages')):
    os.makedirs(os.path.join(basePath, 'bmimages'))
if not os.path.exists(os.path.join(basePath, 'bmimagesResized')):
    os.makedirs(os.path.join(basePath, 'bmimagesResized'))
if not os.path.exists(os.path.join(basePath, 'montages')):
    os.makedirs(os.path.join(basePath, 'montages'))
if not os.path.exists(os.path.join(basePath, 'facesDetected')):
    os.makedirs(os.path.join(basePath, 'facesDetected'))
if not os.path.exists(os.path.join(basePath, 'config')):
    os.makedirs(os.path.join(basePath, 'config'))

def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)

# Function defined for resize and crop of an image
def resize_and_crop(img_path, modified_path, size, crop_type='top'):
    """
    Resize and crop an image to fit the specified size.
    args:
        img_path: path for the image to resize.
        modified_path: path to store the modified image.
        size: (width, height) tuple. Eg (300,300)
        crop_type: can be 'top', 'middle' or 'bottom'
    raises:
        Exception: if can not open the file in img_path of there is problems
            to save the image.
        ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]),
                Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, (img.size[1] - size[1]) / 2, img.size[0], (img.size[1] + size[1]) / 2)
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((size[1] * img.size[0] / img.size[1], size[1]),
                Image.ANTIALIAS)
        # Switch for where to crops
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = ((img.size[0] - size[0]) / 2, 0, (img.size[0] + size[0]) / 2, img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    else :
        img = img.resize((size[0], size[1]),
                Image.ANTIALIAS)
    img.save(modified_path)



# Set up your sparql endpoint
sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql")

# Set your query
sparql.setQuery("""PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX crm: <http://erlangen-crm.org/current/>
PREFIX fts: <http://www.ontotext.com/owlim/fts#>
PREFIX bmo: <http://collection.britishmuseum.org/id/ontology/>

SELECT DISTINCT ?image
WHERE {
  ?object bmo:PX_object_type ?object_type .
  ?object_type skos:prefLabel "bust" .
  ?object bmo:PX_has_main_representation ?image .
} LIMIT 100""")

# Return the JSON triples
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# Open the file for writing urls (this is for image magick)
listImages = open('config/files.txt', 'w')


# Iterate over the results
for result in results["results"]["bindings"]:
    image = result["image"]["value"]
    if os.path.isfile(os.path.join('bmimages', os.path.basename(image))):
        print "File already exists"
    else:
        path = os.path.join('bmimages', os.path.basename(image))
        urllib.urlretrieve(image, path)
        print "Image " + os.path.basename(image) + " downloaded"

for file in os.listdir('bmimages'):
    if not file.startswith('.'):
        listImages.write(os.path.join('bmimagesResized', os.path.basename(file)) + "\n")

make_executable("config/files.txt")

# Iterate through files and crop as required
for file in os.listdir('bmimages'):
    # Make sure file is not a hidden one etc
    if not file.startswith('.') and os.path.isfile(os.path.join('bmimages', file)):
        # Open the file checking if it is valid or not. It fails otherwise :-(
        try:
            if not os.path.exists(os.path.join('bmimagesResized', file)):
                resize_and_crop(os.path.join('bmimages', file), os.path.join('bmimagesResized', file), (300, 300))
                print file + " resized"
            else:
                print "Resized file exists"
        except:
            pass

cascPath = "opencv/haarcascade_frontalface_default.xml"

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

for file in os.listdir('bmimages'):
    if not file.startswith('.'):
        print os.path.join(basePath, 'bmimages', file)
        image = cv2.imread(os.path.join(basePath, 'bmimages', file))


        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(150, 150),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        left = 10
        right = 10
        top = 10
        bottom = 10
        if(len(faces) > 0):
            for (x, y, w, h) in faces:
                image  = image[y-top:y+h+bottom, x-left:x+w+right]
                filename = "facesDetected/cropped_{1}_{0}".format(str(file),str(x))
                if not os.path.exists(filename):
                    cv2.imwrite(filename, image)


# Iterate through files and crop as required
for file in os.listdir('facesDetected'):
    # Make sure file is not a hidden one etc
    if not file.startswith('.') and os.path.isfile(os.path.join('facesDetected', file)):
        # Open the file checking if it is valid or not. It fails otherwise :-(
        try:
            if not os.path.exists(os.path.join('facesDetected', file)):
                resize_and_crop(os.path.join('facesDetected', file), os.path.join('facesDetected', file), (300, 300))
                print file + " resized"
            else:
                print "Resized file exists"
        except:
            pass

def create_montage( file, path ):
    # Create the montage if file exists with a try catch block
    if os.path.isfile(file):
        print "File exists"
        try:
            # Make sure you are in correct directory
            # This will produce multiple tiles for large results
            # Make sure you are in correct directory
            subprocess.call("montage -border 0 -geometry 660x -tile 10x8 @" + file + " montages/bmPortraitBusts.jpg", shell=True)
            subprocess.call("montage -border 0 -geometry 660x -tile 10x8 facesDetected/* montages/bmPortraitBustsFaces.jpg", shell=True)
        except:
            print "Montage generation failed"

create_montage("files.txt", os.path.join(basePath, "config"))
