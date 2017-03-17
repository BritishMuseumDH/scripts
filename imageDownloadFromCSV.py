#!/usr/bin/env python
## Download and repurpose images from Twitter profiles
## Daniel Pett 15/3/2017
__author__ = 'portableant'
## Tested on Python 2.7.13

import urllib
import os
import csv
from PIL import Image
import argparse
import subprocess
import math
from colorthief import ColorThief
import colorsys

parser = argparse.ArgumentParser(description='A script for manipulating Twitter images into a grid')

parser.add_argument('-p', '--path', help='The path to the folder to process', required=True)
# An example would be: --path '/Users/danielpett/Documents/research/twitter/csv/'

parser.add_argument('-d', '--destination', help='The destination folder', required=True)
# An example would be: --destination '/Users/danielpett/Documents/research/twitter/images/'

parser.add_argument('-f', '--filename', help='The file you want to use', required=True)
# An example would be --filename 'bm.users.csv'

# Parse arguments
args = parser.parse_args()
path = args.path

if not os.path.exists(args.destination):
    os.makedirs(args.directory)

resizePath = os.path.join(args.destination, 'resized/')


if not os.path.exists(resizePath):
    os.makedirs(resizePath)

montagePath = os.path.join(args.destination, 'montages/')

if not os.path.exists(montagePath):
    os.makedirs(montagePath)

# Read your CSV file generated from the Rstats scrape - see https://github.com/BritishMuseumDH/BMTwitter
with open(os.path.join(args.path,args.filename), 'rb') as f:
    reader = csv.reader(f)
    csvlines = map(tuple, reader)
    imagesTuple = [x[24] for x in csvlines]

print "CSV file has been parsed"

# Go through the images tuple and get what you want
for i in imagesTuple:
    # The Twitter api replies with scaled down images. We don't want that, no, because that sucks.
    image = i.replace('_normal','')
    # Download each image
    urllib.urlretrieve(image, os.path.join(args.destination,os.path.basename(image)))

print "Images downloaded from Twitter"

# Now make sure they are all in the right dimensions. No outliers. Not too big, not too small. Just right, yeeha.
for file in os.listdir(args.destination):
    # Make sure file is not a hidden one etc
    if not file.startswith('.') and os.path.isfile(os.path.join(args.destination, file)):
        # Open the file checking if it is valid or not. It fails otherwise :-(
        try:
            im = Image.open(args.destination + file)
            # Resize and save the image
            imResize = im.resize((300, 300), Image.ANTIALIAS)
            fileResized = resizePath + file
            imResize.save(fileResized, 'JPEG', quality=90)
        except:
            pass

print "Images resized to dimensions requested - 300x300"

# Change to the resize directory
os.chdir(resizePath)

# Rename files for dodgy string
filenames = os.listdir(os.getcwd())
for filename in filenames:
    os.rename(filename, filename.replace("-", "").lower())
print "Files with file names that break renamed - can probably do better than this?"

# I wanted rows of 10 images
count = round(len([name for name in os.listdir('.') if os.path.isfile(name)]),-1)
tile = '10x' + str(math.ceil(count/10))

# Call the subprocess for imagemagick to create a mosaic
subprocess.call( ['montage', '-border','0', '-geometry', '660x', '-tile', tile, '*', '../montages/finalTile.jpg'] )
# Voila, you should have a tile

print "Montage of users created"

list = []
# Create list of elements of the type [filename, dominant colours]
for file in os.listdir(resizePath):
    if not file.startswith('.') and os.path.isfile(os.path.join(args.destination, file)):
        # Open the file checking if it is valid or not. It fails otherwise :-(
        try:
            colour_thief = ColorThief(file)
            dominant_colour = colour_thief.get_color(quality=1)
            duo = [file, dominant_colour]
            list.append(duo)
        except:
            os.remove(file)
            pass

# Sort this list by hue
sorted_by_colour = sorted(list, key=lambda rgb: colorsys.rgb_to_hls(*rgb[1]))

print "Images sorted by hue"

# Change to the resize directory
os.chdir(resizePath)

# Now make a list just of the filenames, in sorted order
filenames_only = [os.path.join('../images/resized',item[0]) for item in sorted_by_colour]
listImages = open('files.txt', 'w')
listImages.write(' \n'.join(str(i) for i in filenames_only))

print "List of files for image magick use created"

# Change to the config directory
os.chdir(os.path.join(args.path, "../config"))

# Make a montage sorted by hue of the image
subprocess.call("montage @files.txt -border 0 -geometry 660x -tile 10x8 ../images/montages/hues.jpg", shell=True)

print "Montage of images sorted by hues created"

# Remove the files.txt as you do not need it now
os.remove(os.path.join(resizePath, "files.txt"))

print "Removed files.txt until next time you run the script"
