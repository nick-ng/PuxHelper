import PuxGlobal
import BFun
from PuxBulletf import PuxBullet
from PuxShowf import PuxShow
import json
import operator
import time
import math
import threading
import random
import os
import shutil

globalPBullet = PuxBullet(sendOnly=False)
globalThreadReport = {}

class PushBulletT(threading.Thread):
	def __init__(self):
		super(PushBulletT, self).__init__()
		global globalPBullet
		self.pBullet = globalPBullet
		self.threadInitTic = BFun.tic()
	
	def torrentCommand(self,arguments,sender):
		# Trim completed torrents
		orMore = ''
		while len(PuxGlobal.globalRecentCompleteTorrents) > 10:
			PuxGlobal.globalRecentCompleteTorrents.pop(0)
			orMore = '+'
		# Build some strings
		completeBody = ''
		currentBody = ''
		if len(PuxGlobal.globalRecentCompleteTorrents) > 0:
			completeBody = 'Completed:'
		for completeDictionary in PuxGlobal.globalRecentCompleteTorrents:
			show = completeDictionary['show']
			epNum = completeDictionary['epNum']
			tic = completeDictionary['tic']
			tocString = BFun.toc2Str(tic)
			temp = '\n%s Ep%d (%s ago)'%(show,epNum,tocString)
			completeBody = completeBody+temp
		currentKeys = list(PuxGlobal.globalCurrentTorrentsProgress.keys())
		#currentBody = 'Transferring:'
		currentCounter = 0
		for showName in currentKeys:
			for episodeDict in PuxGlobal.globalCurrentTorrentsProgress[showName]:
				temp = '\n%0.0f%% - Ep%d of %s'%(episodeDict['percent'],episodeDict['epNum'],showName)
				currentBody = currentBody+temp
				currentCounter = currentCounter + 1
		if currentCounter > 0:
			currentBody =  'Transferring %d:'%currentCounter + currentBody
		body = ''
		if len(arguments) > 0:
			allArguments = ''.join(arguments).lower()
			if 'all' in allArguments:
				body = completeBody+'\n'+currentBody
			else:
				if 'complete' in allArguments:
					body = completeBody
				if 'current' in allArguments:
					# If no torrents are in progress, leave body empty.
					if (len(body) > 0) and (len(currentBody) > 0):
						body = body+'\n'
					body = body+currentBody
		else:
			if len(completeBody) > 0:
				body = completeBody
			else:
				body = currentBody
		# If body is still empty after everything, add a message
		if len(body) == 0:
			body = 'No torrents to report.'
		title = None
		self.pBullet.sendNote(title,body,sender)
	
	def joinCommand(self,arguments,sender):
		PuxGlobal.joinPlease[0] = True
		print('PuxGlobal.joinPlease[0] set to True')
		title = None
		body = 'Join requested.'
		self.pBullet.sendNote(title,body,sender)
	
	def upgradeCommand(self,arguments,sender):
		upgrade = -1
		title = None
		report = ' '
		if len(arguments) == 0:
			upgrade = 0
		elif arguments[0].lower() == 'please':
			# Perform upgrade.
			fileList = os.listdir(PuxGlobal.UPGRADE_PATH)
			#currentDir = os.getcwd()
			currentDir = PuxGlobal.PROGRAM_PATH
			report = ' Copying %d files to %s'%(len(fileList),currentDir)
			for aFile in fileList:
				sourcePath = PuxGlobal.UPGRADE_PATH+'/'+aFile
				if os.path.isfile(sourcePath):
					BFun.ezLog('Copying %s'%sourcePath)
					shutil.copy(sourcePath,currentDir)
			upgrade = 1
		else:
			upgrade = 0
		if upgrade == 0:
			body = "Correct usage is push/pull upgrade please. It's a safety feature."
		elif upgrade == 1:
			body = 'Upgrade complete. Join requested.'+report
			PuxGlobal.joinPlease[0] = True
			print('PuxGlobal.joinPlease[0] set to True')
		else: # Upgrade not 1 or 0 means something went wrong.
			body = 'Error when upgrading. Code %d'%upgrade
			BFun.ezLog(body)
		self.pBullet.sendNote(title,body,sender)

	def invalidCommand(self,wholeCommand,sender):
		body = "%s is not a valid command"%wholeCommand
		body = ' '.join(body.split())
		self.pBullet.sendNote(None,body,sender)
	
	def runtimeCommand(self,sender):
		global globalThreadReport
		body = 'PuxHelper has been running for %s.'%BFun.toc2Str(self.threadInitTic)
		keyList = list(globalThreadReport.keys())
		body = body+'\n%d Threads:'%len(keyList)
		for aKey in keyList:
			reportTime = globalThreadReport[aKey]
			body = body+'\n%s ago, %s'%(BFun.toc2Str(reportTime),aKey)
		self.pBullet.sendNote(None,body,sender)
		
	def run(self):
		global globalThreadReport
		while not PuxGlobal.joinPlease[0]:
			globalThreadReport['PushBullet'] = BFun.tic()
			print('Getting new pushes...')
			a = BFun.tic()
			commandList = self.pBullet.commandFinder()
			if len(commandList) > 0:
				print('Found %d commands'%len(commandList))
			for aDict in commandList:
				sender = aDict['sender']
				arguments = aDict['arguments']
				try:
					command = arguments.pop(0)
				except:
					command = ''
				commandLower = command.lower()
				if commandLower == 'speak':
					title = None
					body = 'Woof!'
					if len(arguments) > 0:
						if (arguments[0].lower() == 'jpn') or ('japan' in arguments[0].lower()):
							body = 'Wan!'
					print('Sending message')
					self.pBullet.sendNote(title,body,sender)
				elif 'torrent' in commandLower:
					self.torrentCommand(arguments,sender)
				elif 'join' in commandLower:
					self.joinCommand(arguments,sender)
				elif 'upgrade' in commandLower:
					self.upgradeCommand(arguments,sender)
				elif 'run' in commandLower:
					self.runtimeCommand(sender)
				else:
					wholeCommand = command+' '+' '.join(arguments)
					self.invalidCommand(wholeCommand,sender)
			# End of commands
			print('Took %0.1f seconds to check and process pushes'%BFun.toc(a))
			print('Sleeping for %0.0f seconds. (%d rates left)'%(self.pBullet.sleepTime,self.pBullet.previousRates))
			time.sleep(self.pBullet.sleepTime) # Wait to avoid getting ratelimited
		
class TorrentT(threading.Thread):
	def __init__(self):
		super(TorrentT, self).__init__()
		global globalPBullet
		self.pBullet = globalPBullet
		self.showList = []
		self.counters = {'add': 0, 'check': 0}
		self.counterFreq = {'add': 3607, 'check': 3} # All prime numbers 'cause
		self.TORRENT_LIST_PATH = PuxGlobal.CONFIG_PATH+'/torrentList.txt'
		self.previousTorrentListHash = '1'
	
	def advanceCounters(self):
		keys = list(self.counters.keys())
		for key in keys:
			self.counters[key] = (self.counters[key] + 1) % self.counterFreq[key]
		time.sleep(1)
	
	def addShows(self):
		# Load torrent list
		temp = BFun.ezRead(self.TORRENT_LIST_PATH)
		temp = temp.splitlines()
		# Delete old showList (for memory?) and make a new one.
		for show in self.showList:
			# Make sure all data is saved.
			show.saveData()
		self.showList.clear()
		self.showList = []
		for s in temp:
			# Check for comments
			s2 = s.split()
			if len(s2) > 0:
				if '**' in s2[0]:
					print('Comment')
				else:
					self.showList.append(PuxShow(s,self.pBullet))
					print('Added %s'%s2[0])
			else:
				print('Empty line')
		for show in self.showList:
			show.newTorrentURLs()
			# Update global variables
			show.checkTorrents()

	def checkTorrentList(self):
		currentHash = BFun.ezHash(self.TORRENT_LIST_PATH)
		if self.previousTorrentListHash != currentHash:
			self.previousTorrentListHash = currentHash
			self.counters['add'] = 0

	def run(self):
		global globalThreadReport
		try:
			while not PuxGlobal.joinPlease[0]:
				globalThreadReport['Torrent'] = BFun.tic()
				self.checkTorrentList()
				if self.counters['add'] == 0:
					print('Updating show list')
					self.addShows()
				if self.counters['check'] == 0:
					for show in self.showList:
						print('Checking torrents of '+show.SHOW_NAME)
						try:
							show.checkTorrents()
						except:
							print('Something went wrong. Probably Transmission down?')
							self.counters['add'] = self.counterFreq['add'] - 1
				self.advanceCounters()
		except:
			BFun.ezLog('Torrent thread broke',ex)
		# If it gets to here, it means we're trying to join.
		for show in self.showList:
			# So make sure all data is saved.
			show.saveData()


