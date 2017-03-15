#!/usr/bin/python
## Split audio files into chunks
## Daniel Pett 15/3/2017
__author__ = 'portableant'
## Tested on Python 2.7.13

import argparse
import os
from pydub import AudioSegment
from pydub.utils import make_chunks

parser = argparse.ArgumentParser(description='A script for splitting audio files into segements')
parser.add_argument('-p', '--path', help='The path to the folder to process', required=True)
# An example would be: --path '/Users/danielpett/githubProjects/britishMuseumSoundCloud/originals/unprocessed/'
parser.add_argument('-d', '--destination', help='The destination folder', required=True)
# An example would be: --path '/Users/danielpett/githubProjects/britishMuseumSoundCloud/chunked/'
parser.add_argument('-l', '--length', help='Length of chunk', required=True)
# An example would be --length 10000

# Parse arguments
args = parser.parse_args()
path = args.path

# Loop through the files
for file in os.listdir(path):
    print('Now processing: ' + file)
    myaudio = AudioSegment.from_file(os.path.join(path,file), "mp3")
    # Make chunks of length specified
    chunk_length_ms = args.length
    chunks = make_chunks(myaudio, int(args.length))
    for i, chunk in enumerate(chunks):
        processedFileName = os.path.splitext(file)[0]
        chunk_name = args.destination + processedFileName + "_Chunk{0}.mp3".format(i)
        print "Now exporting: " , chunk_name
        chunk.export(chunk_name, format="mp3")
