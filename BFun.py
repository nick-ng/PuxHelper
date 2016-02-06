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
import traceback

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

def now2Str():
	aNow = time.localtime()
	YYYY = '%d'%aNow.tm_year
	MM = '%02d'%aNow.tm_mon
	DD = '%02d'%aNow.tm_mday
	hh = '%02d'%aNow.tm_hour
	mm = '%02d'%aNow.tm_min
	ss = '%02d'%round(aNow.tm_sec)
	return YYYY+'-'+MM+'-'+DD+' '+hh+':'+mm+':'+ss

def omniDecode(someBytes):
	global globalEncodingList
	for n in range(len(globalEncodingList)):
		try:
			#return someBytes.decode('utf-8')
			return someBytes.decode(globalEncodingList[n])
		except UnicodeDecodeError as ex:
			# Couldn't decode so try next codec
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
	except FileNotFoundError as ex:
		tempObject = open(somePath,'w')
		someString = ''
	tempObject.close()
	return someString

def ezAppend(somePath,someString):
	# Append to a file. Will create a file if it doesn't exist.
	tempObject = open(somePath,'a')
	tempObject.write(someString)
	tempObject.close()

def ezLog0(someString,ex=None):
	timeStr = now2Str() + ': '
	reStr = timeStr + someString
	if ex:
		tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
		tb_text = ''.join(tb_lines)
		reStr = reStr + '\n' + tb_text
	return reStr+'\n'

def ezLog(someString,ex=None):
	ezAppend(PuxGlobal.LOG_PATH,ezLog0(someString,ex))
	
# Opens URL and decodes webpage source.
def webRead(someURL,timeout=19,retrys=3):
	#temp = urllib.request.urlopen(someURL)
	#return omniDecode(temp.read())
	counter = 0
	while counter < retrys:
		try:
			tempR = requests.get(someURL,timeout=timeout)
			return tempR.text
		except requests.exceptions.ConnectTimeout as ex:
			counter += 1
			print('Timed out while opening %s. %d times'%(someURL,counter))
	ezLog('Timed out trying to open %s (%d tries)'%(someURL,retrys))
	return 'timed out'
	
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
