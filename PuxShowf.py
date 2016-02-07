import PuxGlobal
import BFun
import transmissionrpc
import re
import os
import time
import PuxTorrents
import shutil
import urllib.request
import requests
from PuxBulletf import PuxBullet

'''
Notes:
Save and load self.torrentList to a json with:
BFun.jSaver(someJSON,somePath)
someJSON = BFun.jLoader(somePath)

'''

#global PuxGlobal.globalRecentCompleteTorrents # List of dictionaries
#global PuxGlobal.globalCurrentTorrentsProgress # Dictionary of list of dictionaries

class PuxShow:
	# Pre define some functions so things work?
	#def findLatestEpisode(self):
		#pass
	# Class to handle show torrents, files on server etc.
	def __init__(self, torrentLine, PuxBulletObject):
		# Initialise PuxShow class
		self.pBullet = PuxBulletObject
		self.TILDA = os.environ['HOME'] # Home directory of linux
		self.SERVER_PATH = PuxGlobal.SERVER_PATH
		self.LOCAL_PATH = PuxGlobal.LOCAL_PATH
		self.CONFIG_PATH = PuxGlobal.CONFIG_PATH
		self.DATA_PATH = PuxGlobal.DATA_PATH
		self.DOWNLOAD_PATH = self.LOCAL_PATH+'/torrentDL'
		self.transmissionSession = PuxTorrents.connectTransmission()
		# Decode torrentLine
		# * Show Name*Show URL*File Extension*Parent Directory*Max Size (MB)*Min Size (kB)*episodeOverride
		# 0           1        2              3                4             5             6
		lineParts = torrentLine.split('*')
		self.SHOW_NAME = lineParts[0]
		self.SHOW_URL = lineParts[1]
		self.EXTENSION = lineParts[2]
		self.SHOW_PATH = self.SERVER_PATH+'/'+lineParts[3]+'/'+self.SHOW_NAME
		self.LATEST_DATA_PATH = self.DATA_PATH+'/'+self.SHOW_NAME+'_Latest.txt'
		self.TORRENT_LIST_PATH = self.DATA_PATH+'/'+self.SHOW_NAME+'_torrentList.txt'
		#self.latestEpisode = self.findLatestEpisode()
		self.torrentList = [] # Empty list
		self.requestSleep = 1.1 # Time to sleep between requests.
		self.updateTorrentList()
		try:
			latestEpOverride = int(lineParts[6])
		except IndexError as ex:
			# Option not present. Start from episode 0
			latestEpOverride = 0
		except ValueError as ex:
			# Option present but incorrect. Log and start from episode 0
			BFun.ezLog('%s entry in torrentlist.txt is incorrect. Override value should be integer'%self.SHOW_NAME)
			latestEpOverride = 0
		self.latestEpisode = -1
		self.findLatestEpisode(latestEpOverride)
		print('self.latestEpisode = %d'%self.latestEpisode)
		self.MAX_FILE_SIZE = int(lineParts[4])*1024*1024 # in bytes
		self.MIN_FILE_SIZE = int(lineParts[5])*1024 # in bytes
		self.pendingTorrents = False
	
	def getExcludeList(self):
		# Get list of *_exclude.txt files from config directory.
		configFileList = os.listdir(self.CONFIG_PATH)
		excludeFileList = []
		for fn in configFileList:
			if '_exclude.txt' in fn.lower(): # Don't get other files like torrentList.txt
				subStrings = fn.split('_')
				excludeFileList.append(subStrings[0]) # Add the name of the site the file is for.
				self.EXCLUDE_PATH = False
		for subStr in excludeFileList:
			if subStr.lower() in self.SHOW_URL.lower():
				excludePath = self.CONFIG_PATH+'/'+subStr+'_exclude.txt'
				return BFun.ezRead(excludePath).splitlines()
		return [] # if file doesn't exist, return empty list

	def findLatestEpisode(self,override=0):
		#  Latest episode based on own records (torrentList json file)
		tempLatestEp = -1
		if len(self.torrentList) > 0:
			for torrentDict in self.torrentList:
				if torrentDict['epNum'] > tempLatestEp:
					tempLatestEp = torrentDict['epNum']
			print('Latest torrent in torrent list = %d'%tempLatestEp)
		if override > tempLatestEp:
			self.latestEpisode = override
			print('self.latestEpisode = %d'%self.latestEpisode)
			return self.latestEpisode
		else:
			self.latestEpisode = tempLatestEp
			print('self.latestEpisode = %d'%self.latestEpisode)
			return self.latestEpisode
		# ===========================
		# Maybe later. Probably never
		# ===========================
		# Find latest episode in directory.
		try:
			# Try to get file list from show folder on file server.
			fileList = os.listdir(self.SHOW_PATH)
		except FileNotFoundError as ex:
			# Make the directory
			os.mkdir(self.SHOW_PATH)
			fileList = []
		# Maybe put in a file?
		notEpNums = BFun.ezRead(self.CONFIG_PATH+'/PuxShow_notEpNums.txt').splitlines()
		for fileName in fileList:
			fileName2 = fileName.lower()
			for ss in notEpNums:
				fileName2.replace(ss,'')
			numbers = re.findall(r'\d+',fileName2)
			if len(numbers) > 0:
				epNumGuess = int(numbers[-1]) # It's probably the last number we found
		# _Latest.txt files replaced with override input.
		# Find latest episode from data file
		try:
			# Load data file (e.g. /Data/Come Home Love_Latest.txt)
			dataFile = open(self.LATEST_DATA_PATH,'r')
			dataLatest = int(dataFile.read())
			dataFile.close()
		except FileNotFoundError as ex:
			# Couldn't read file
			dataFile = open(self.LATEST_DATA_PATH,'w')
			dataFile.write('-1') # Write -1
			dataFile.close()
			dataLatest = -1
		except ValueError as ex:
			# Didn't contain an integer
			dataLatest = -1
		if dataLatest < directoryLatest:
			dataFile = open(self.LATEST_DATA_PATH,'w')
			dataFile.write(directoryLatest) # Update data file
			dataFile.close()
			self.latestEpisode = directoryLatest
		else:
			self.latestEpisode = dataLatest
				
	def newTorrentURLs(self,test=False):
		# Find the latest torrent URLs, add them (paused) to Transmission and check their size.
		excludeList = self.getExcludeList()
		searchDict = {} # Empty dictionary
		searchDict['URL'] = self.SHOW_URL
		#searchDict['extension'] = self.EXTENSION
		foundTorrents = PuxTorrents.torrentSearch(searchDict)
		urlList = []
		tempEpNum = -1
		for t in foundTorrents: # tuples in foundTorrents
			epNum = t[0]
			url = t[1]
			alreadyAdded = False
			if epNum <= self.latestEpisode:
				print('Already have episode %d'%epNum)
				alreadyAdded = True
			else:
				for torrentDict in self.torrentList:
					if torrentDict['URL'] == url:
						print('Already added URL')
						alreadyAdded = True
			if not alreadyAdded:
				print('Processing %s ep %d'%(self.SHOW_NAME,epNum))
				#aa = BFun.tic()
				# add_torrent() will return control once it has finished adding the torrent.
				print('Getting .torrent...')
				torrentRetrys = 0
				gotTorrent = False
				while torrentRetrys < 99:
					try:
						self.requestSleep += 1.1
						print('Sleeping %0.1f seconds before retrieving torrent'%self.requestSleep)
						time.sleep(self.requestSleep)
						#r = requests.get(url,timeout=10)
						fileLikeObject = urllib.request.urlopen(url, None, 30)
						gotTorrent = True
						break
					except urllib.error.URLError as ex:
						if 'error timed out' in str(ex).lower():
							torrentRetrys += 1
							print('Timed out. Trying again. %d'%torrentRetrys)
						else:
							BFun.ezLog('Error when retrieving .torrent file. Search for 9217568',ex)
					except Exception as ex:
						BFun.ezLog('Error when retrieving .torrent file. Search for 3195897',ex)
				if gotTorrent:
					# Write data to .torrent file. 
					localURI = self.DATA_PATH+'/lastTorrent.torrent'
					fo = open(localURI,'wb') # Gets overwritten.
					#fo.write(r.content)
					shutil.copyfileobj(fileLikeObject, fo)
					fo.close()
					try:
						# .torrent file may be bad?
						torrent = self.transmissionSession.add_torrent(localURI,paused=True)
						hashString = torrent.hashString
						torrentContents = self.transmissionSession.get_torrent(hashString).files()
					except Exception as ex:
						BFun.ezLog('Error when sending .torrent file to transmission. Search for 4523861',ex)
						# Add bogus torrent to torrentList with URL and Completed.
						# Skip the URL now but don't mark it so we can try it later.
						torrentDict = {'URL': 'a', 'completed': 1, 'epNum': -epNum, 'hashString': 'brokenURL', 'wantedFileIDs': [], 'comment': ['ep %d'%epNum,'brokenURL',url]}
						self.torrentList.append(torrentDict)
						self.saveData()
						torrentContents = [] # Empty list so it won't be processed
						# Log what happened.
						BFun.ezLog('Bad .torrent file from %s. (ep %d, %s)'%(url,epNum,localURI))
					time.sleep(2)
				else:
					print("Didn't get torrent after 99 retrys.")
					break
				# Get the unique hash of the torrent so working with torrents is easier.
				#tSess2.get_torrent(hashString).files()
				fileInfos = []
				wantedFiles = []
				unwantedFiles = []
				# Check if torrent has files we want.
				desiredTorrent = False
				for m in range(len(torrentContents)):
					desiredFile = True
					fileName = torrentContents[m]['name']
					fileSize = torrentContents[m]['size']
					nameSubs = fileName.split('.')
					if nameSubs[-1].lower() in self.EXTENSION.lower(): # self.EXTENSION has the '.'
						print('Processing %s'%fileName)
						if fileSize > self.MAX_FILE_SIZE:
							desiredFile = False
							print('File %d too big'%m)
						if fileSize < self.MIN_FILE_SIZE:
							desiredFile = False
							#print('File %d too small'%m)
						for exSubString in excludeList:
							if exSubString.lower() in fileName.lower():
								desiredFile = False
								print('Found %s in %s'%(exSubString,fileName))
					else:
						desiredFile = False
						#print('File %d has wrong extension'%m)
					if desiredFile:
						desiredTorrent = True
						wantedFiles.append(m)
					else:
						unwantedFiles.append(m)
				if len(wantedFiles) > 8:
					# If there are more than 8 files, it's a compliation torrent which we don't want.
					# There may be week's worth of episodes which is ok.
					desiredTorrent = False
					print('Found %d files. Rejecting'%len(wantedFiles))
				print('unwantedFiles:')
				print(unwantedFiles)
				# If torrentContents has no items, it's because it wasn't added. Check "unique hash" for human readable description
				if len(torrentContents) > 0:
					self.transmissionSession.change_torrent(hashString, files_unwanted=unwantedFiles)
					self.transmissionSession.change_torrent(hashString, files_wanted=wantedFiles)
				if desiredTorrent:
					urlList.append(url)
					# If it's a behind the scenes or something, don't change the actual episode number.
					if epNum != 9999999:
						print('Found episode %d'%epNum)
						tempEpNum = max([epNum,tempEpNum]) # Largest number in the found torrents.
					else:
						epNum = -1
					if test:
						# We're just testing so remove the torrent.
						self.transmissionSession.remove_torrent(hashString, delete_data=True)
					else:
						# Start the torrent
						self.transmissionSession.start_torrent(hashString)
						self.pendingTorrents = True
						# Add to self.torrentList
						torrentDict = {}
						torrentDict['hashString'] = hashString
						torrentDict['wantedFileIDs'] = wantedFiles
						# 0 = still downloading. -1 = complete on Transmission, not moved to fileserver. 1 = moved to fileserver, removed from transmission
						torrentDict['completed'] = 0
						torrentDict['URL'] = url
						torrentDict['epNum'] = epNum
						self.torrentList.append(torrentDict)
						BFun.jSaver(self.torrentList,self.TORRENT_LIST_PATH)
				else:
					# Not a torrent we want so remove from transmission.
					if len(torrentContents) > 0:
						self.transmissionSession.remove_torrent(hashString, delete_data=True)
						# and Add bogus torrent to torrentList with URL and Completed so we don't download it again.
						torrentDict = {'URL': url, 'completed': 1, 'epNum': -epNum, 'hashString': 'noFiles', 'wantedFileIDs': []}
						self.torrentList.append(torrentDict)
						self.saveData()
		if tempEpNum > self.latestEpisode: # Update latest episode number
			print('tempEpNum = %d'%tempEpNum)
			self.latestEpisode = tempEpNum
			#dataFile = open(self.LATEST_DATA_PATH,'w')
			#dataFile.write('%d'%tempEpNum)
			#dataFile.close()
			print('Updated data file')
		if test:
			return urlList
		else:
			return urlList
	
	def checkTorrents(self):
		#global PuxGlobal.globalRecentCompleteTorrents # List of dictionaries
		#global PuxGlobal.globalCurrentTorrentsProgress # Dictionary of list of dictionaries
		# Reduce self.requestSleep.
		if self.requestSleep > 1:
			self.requestSleep = self.requestSleep - 1
		progressList = [] # [{'percent}]
		for torrentDict in self.torrentList:
			if torrentDict['completed'] < 1:
				# refresh the information about the torrent.
				fileDicts = self.transmissionSession.get_torrent(torrentDict['hashString']).files()
				#self.DOWNLOAD_PATH
				sizeList = []
				completeList = []
				for n in torrentDict['wantedFileIDs']:
					sizeList.append(int(fileDicts[n]['size']))
					completeList.append(int(fileDicts[n]['completed']))
				totalSize = sum(sizeList)
				totalComplete = sum(completeList)
				if totalComplete == totalSize:
					# Append to globalRecentCompleteTorrents
					completeDictionary = {}
					completeDictionary['show'] = self.SHOW_NAME
					completeDictionary['epNum'] = torrentDict['epNum']
					completeDictionary['tic'] = BFun.tic()
					PuxGlobal.globalRecentCompleteTorrents.append(completeDictionary)
					# Move files to fileServer
					# Make sure directory exists
					try:
						# Try to get file list from show folder on file server.
						temp = os.listdir(self.SHOW_PATH)
					except FileNotFoundError as ex:
						# Make the directory
						os.mkdir(self.SHOW_PATH)
					for n in torrentDict['wantedFileIDs']:
						fileName = fileDicts[n]['name']
						startPath = self.DOWNLOAD_PATH+'/'+fileName
						endPath = self.SHOW_PATH
						print('Copying %s Ep %d'%(completeDictionary['show'],completeDictionary['epNum']))
						shutil.copy(startPath, endPath)
						torrentDict['completed'] = -1
						BFun.jSaver(self.torrentList,self.TORRENT_LIST_PATH)
						print('Finished copying')
						time.sleep(0.1) # Sleep for no reason?
						# Remove torrent and files from transmission
						self.transmissionSession.remove_torrent(torrentDict['hashString'], delete_data=True)
						torrentDict['completed'] = 1
						BFun.jSaver(self.torrentList,self.TORRENT_LIST_PATH)
					tempBody = self.SHOW_NAME+' Ep: %d complete'%torrentDict['epNum']
					self.pBullet.sendBrowsers(body=tempBody)
				else:
					# Add progress to progressDictionary
					progressDictionary = {}
					progressDictionary['epNum'] = torrentDict['epNum']
					progressDictionary['percent'] = 100.*totalComplete/totalSize
					progressList.append(progressDictionary)
		PuxGlobal.globalCurrentTorrentsProgress[self.SHOW_NAME] = progressList
	
	def updateTorrentList(self):
		# Consolidate torrents in transmission, previously completed torrents and
		# torrents already in torrentList
		# Load torrents from data file
		fileTorrents = BFun.jLoader(self.TORRENT_LIST_PATH,expectList=True)
		if len(self.torrentList) == 0:
			self.torrentList = fileTorrents
		else:
			consolidatedTorrents=[]
			hashList = []
			for sTorrent in self.torrentList:
				hashList.append(sTorrent['hashString'])
			for fTorrent in fileTorrents:
				hashList.append(fTorrent['hashString'])
			hashSet = set(hashList)
			hashList = set(hashSet)
			for hashString in hashList:
				found = False
				for sTorrent in self.torrentList:
					if hashString == sTorrent['hashString']:
						consolidatedTorrents.append(sTorrent)
						found = True
						break
				if found == False:
					for fTorrent in fileTorrents:
						if hashString == fTorrent['hashString']:
							consolidatedTorrents.append(fTorrent)
							break
			self.torrentList = consolidatedTorrents
			BFun.jSaver(self.torrentList,self.TORRENT_LIST_PATH)
			
	def saveData(self):
		BFun.jSaver(self.torrentList,self.TORRENT_LIST_PATH)
