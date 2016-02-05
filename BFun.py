import PuxGlobal
import os
import time
import datetime
import math
import random
import urllib.request
import re
import sys
import json
import requests
import hashlib
import statistics

# Load all character encoding names for OmniDecode later
if sys.platform == 'linux' or sys.platform == 'linux2':
	encodingListFile = open(PuxGlobal.PROGRAM_PATH+'/data/!!encodeList.txt','r')
elif _platform == "darwin":
	print('Program not set up for Mac OS')
elif _platform == "win32":
	encodingListFile = open('data\\!!encodeList.txt','r')
globalEncodingList = encodingListFile.read().splitlines()
encodingListFile.close()

def mean(a):
	if len(a) <= 0:
		return 0
	else:
		return float(sum(a))/len(a)

def median(a):
	if len(a) <= 0:
		return 0
	else:
		return statistics.median(a)

def stdev(a):
	if len(a) <= 0:
		return 0
	else:
		meana = mean(a)
		distances = 0
		for temp in a:
			temp2 = temp - meana
			distances = distances + pow(temp2,2)
		return distances/len(a)

def secondsAgo2Str(someSeconds):
	aMinute = 60.0
	anHour = 60.0*aMinute
	aDay = 24.0*anHour
	if someSeconds > aDay:
		days = someSeconds/aDay
		return '%0.1f days'%days
	elif someSeconds > anHour:
		hours = someSeconds/anHour
		return '%0.1f hr'%hours
	elif someSeconds > aMinute:
		minutes = someSeconds/aMinute
		return '%0.1f min'%minutes
	else:
		return '%0.1f sec'%someSeconds

def tic():
	return time.time()

def toc(a):
	return time.time()-a

def toc2Str(a):
	return secondsAgo2Str(toc(a))

def omniDecode(someBytes):
	global globalEncodingList
	for n in range(len(globalEncodingList)):
		try:
			#return someBytes.decode('utf-8')
			return someBytes.decode(globalEncodingList[n])
		except:
			pass
	print("Couldn't decode bytes")
	return '<error>'

def ezEncode(someString):
	return someString.encode('utf-8','backslashreplace')

def ezPrint(someString):
	print(str(someString).encode('ascii','replace').decode('ascii'))
	return

def ezRead(somePath):
	# Reads a file (in most encodings) and returns its contents as an appropriately encoded string.
	# If the file doesn't exist, creates it and returns an empty string.
	try:
		tempObject = open(somePath,'rb')
		someBytes = tempObject.read()
		someString = omniDecode(someBytes)
	except:
		tempObject = open(somePath,'w')
		someString = ''
	tempObject.close()
	return someString

def ezAppend(somePath,someString):
	# Trys to append to a file. If it can't, it'll write to that file instead.
	try:
		tempObject = open(somePath,'a')
	except:
		tempObject = open(somePath,'w')
	tempObject.write(someString)
	tempObject.close()
	
def ezLog(someString):
	# Appends a string to the log. Prepends time and appends new line as well.
	ezAppend(PuxGlobal.LOG_PATH,'%0.1f '%time.time()+someString+'\n')
	
# Opens URL and decodes webpage source.
def webRead(someURL):
	#temp = urllib.request.urlopen(someURL)
	#return omniDecode(temp.read())
	counter = 0
	while counter < 10:
		try:
			tempR = requests.get(someURL,timeout=10)
			return tempR.text
		except:
			print('Timed out while opening %s. %d times'%(someURL,counter))
	return '%s did not load'%someURL
	
def jSaver(someJSON,somePath):
	tempBytes = ezEncode(json.dumps(someJSON, skipkeys=True, ensure_ascii=False, sort_keys=True))
	fo = open(somePath,'wb')
	fo.write(tempBytes)
	fo.close()
	
def jLoader(somePath,expectList=True):
	tempString = ezRead(somePath)
	if len(tempString) == 0:
		if expectList:
			tempString = '[]'
		else:
			tempString = '{}'
	return json.loads(tempString, 'utf-8')

def ezHash(somePath):
	# Returns the md5 hash of a file
	hasher = hashlib.md5()
	fo = open(somePath, 'rb')
	buf = fo.read()
	fo.close()
	hasher.update(buf)
	return hasher.hexdigest()
