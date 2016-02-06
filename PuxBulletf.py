# PushBullet module for PuxHelper.py
import requests
import json
import BFun
import re
import os
import time
import math
import operator
from requests.auth import HTTPBasicAuth

'''
Notes:
Save and load to json with:
BFun.jSaver(someJSON,somePath)
someJSON = BFun.jLoader(somePath)
'''

class PuxBullet:
	
	def __init__(self,myName='PuxHelper',sendOnly=True):
		self.version = 1
		self.TILDA = os.environ['HOME'] # Home directory of linux
		self.CONFIG_DIRECTORY = self.TILDA+'/Mount/fileServer/PUBLIC/Nick/PythonData/Configs'
		self.getAccessToken()
		self.myName = myName
		self.myIden = None
		self.sleepTime = 1 # Time to sleep between pushes.
		self.pushList = [] # Need to load push list from local file.
		self.ratesPerRequest = [5] # Last n ratesPerRequest
		self.previousRates = -1
		self.seenPushIdens = []
		self.knownDevices = []
		self.browserIdens = []
		self.sendOnly = sendOnly
		self.indicatorList = BFun.ezRead(self.CONFIG_DIRECTORY+'/puxhelper_indicators.txt').lower().splitlines()
		# This should be the last thing in this init.
		if not self.sendOnly:
			print('Getting all pushes.')
			self.refreshPushes(newOnly=False)
		self.getBrowserIdens()
		#self.createThisDevice() # Apparently creating a device is quite a hassle.
	
	def newestPush(self):
		if len(self.pushList) > 0:
			return self.pushList[0]
		else:
			return {}
	
	def getAvgRates(self):
		while min(self.ratesPerRequest) < 1:
			# Remove all rates less than 1
			# Happens when rate resets or during initilisation.
			self.ratesPerRequest.remove(min(self.ratesPerRequest))
		while len(self.ratesPerRequest) > 99:
			# Keep length of stored rates below 100 to maintain speed.
			self.ratesPerRequest.pop()
		# Median is cooler than mean cause it's harder to calculate
		return math.ceil(BFun.median(self.ratesPerRequest))
		
	def getAccessToken(self):
		temp = BFun.ezRead(self.TILDA+'/private/pushbullettoken.txt')
		self.ACCESS_TOKEN = temp.splitlines()[0]

	def puxRequest(self,method, url, postdata=None, params=None, files=None):
		# Makes a request then calculates sleep time to avoid getting ratelimited.
		headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "asdf"}
		if postdata:
			postdata = json.dumps(postdata)
		# Make request and calculate time.
		status_codes = [0]
		while status_codes[-1] != 200:
			timer1 = BFun.tic()
			try:
				r = requests.request(method, url, data=postdata, params=params, headers=headers, files=files, auth=HTTPBasicAuth(self.ACCESS_TOKEN, ""),timeout=30)
				status_codes.append(r.status_code)
			except requests.exceptions.ConnectTimeout as ex:
				print('PushBullet request timedout.')
				status_codes.append(1)
			except Exception as ex:
				BFun.ezLog('Error when making pushbullet request:',ex)
			if status_codes[-1] == 403:
				self.getAccessToken()
			if len(status_codes) > 100:
				print('Failed requests 100 times')
				for d in status_codes:
					print('Status Code %d'%d)
				break
		if not self.sendOnly:
			timeForRequest = BFun.toc(timer1)
			# Update sleep time.
			timeUntilReset = float(r.headers.get('X-Ratelimit-Reset',1)) - time.time()
			remainingRates = int(r.headers.get('X-Ratelimit-Remaining',0))
			self.ratesPerRequest.append(self.previousRates-remainingRates)
			self.previousRates = remainingRates
			remainingRequests = math.floor(1.*remainingRates/self.getAvgRates())
			timeBetweenRequests = 1.*timeUntilReset/remainingRequests
			# Double sleep time so we can run 2. This one and the test one.
			self.sleepTime = 2.*math.ceil(max([timeBetweenRequests - timeForRequest,1]))
		return r

	def host(self,restOfURL):
		return 'https://api.pushbullet.com/v2/'+restOfURL

	def getDevices(self):
		r = self.puxRequest('GET',self.host('devices'))
		return r.json().get('devices',[])
	
	def getBrowserIdens(self):
		devices = self.getDevices()
		for device in devices:
			icon = device.get('icon','')
			if icon.lower() == 'browser':
				# use try except since we don't want messages going to None if we can't get the iden
				try:
					self.browserIdens.append(device['iden'])
				except Exception as ex:
					BFun.ezLog('Error when getting browser idens in PuxBulletf. Search for 1751686',ex)
	
	def createThisDevice(self):
		devices = self.getDevices()
		nickNames = []
		for device in devices:
			nickName = device.get('nickname','')
			if nickName == self.myName:
				self.myIden = device.get('iden',None)
		if self.myIden:
			print('%s already in list. iden: '%(self.myName,self.myIden))
		else:
			print('Creating device %s'%self.myName)
			postdata = {}
			postdata['nickname'] = self.myName
			postdata['model'] = 'Python'
			postdata['manufacturer'] = 'Pux'
			postdata['app_version'] = self.version
			postdata['icon'] = 'system'
			self.puxRequest('POST',self.host('devices'),postdata)
			self.createThisDevice() # Get device iden

	def sendNote(self,title=None,body='See title.',target=None):
		body = '%0.0f sec between checks.\n'%self.sleepTime+body
		postdata = {'type': 'note', 'title': title, 'body': body, 'source_device_iden': self.myIden}
		if target:
			postdata['device_iden'] = target
		return self.puxRequest('POST',self.host('pushes'),postdata)
	
	def sendBrowsers(self,title=None,body='See title.'):
		for iden in self.browserIdens:
			self.sendNote(title,body,iden)
	
	def dismissPush(self,iden):
		postdata = {'dismissed': 'true'}
		return self.puxRequest('POST',self.host('pushes/'+iden),postdata)
	
	def deletePush(self,iden):
		return self.puxRequest('DELETE',self.host('pushes/'+iden))
	
	def refreshPushes(self,newOnly=True):
		params = {'active': 'true'}
		#params = {}
		if newOnly:
			params['modified_after'] = self.newestPush().get('modified',0)
		r = self.puxRequest('GET',self.host('pushes'),params=params)
		tempPushes = r.json().get('pushes')
		if newOnly:
			tempPushes.extend(self.pushList)
			#tempPushes = list(set(tempPushes)) # Remove duplicate pushes
			self.pushList = sorted(tempPushes, key=operator.itemgetter('modified'), reverse=True) # Sort pushes.
		else:
			self.pushList = tempPushes
			# Update the list of seen push idens
			# newOnly = False is only called at initialisation.
			for push in self.pushList:
				self.seenPushIdens.append(push.get('iden',''))
		return r
	
	def commandFinder(self):
		# Returns a list of lists of the form:
		# [[command 1, argument 1, argument 2, etc.], [command 2, argument 1, etc.], etc.]
		r = self.refreshPushes()
		pushes = r.json().get('pushes',[])
		commandList = []
		for push in pushes:
			pushIden = push.get('iden',None)
			if pushIden in self.seenPushIdens:
				pass #
			else:
				#pTitle = push.get('title','No Title') # Don't check title.
				pBody = push.get('body','')
				pBodyS = pBody.split()
				try:
					pBodyS0 = pBodyS.pop(0)
					if pBodyS0.lower() in self.indicatorList:
						sender = push.get('source_device_iden',None)
						commandDict = {}
						commandDict['sender'] = sender
						commandDict['arguments'] = pBodyS
						commandList.append(commandDict)
						if pushIden:
							#self.dismissPush(pushIden)
							self.deletePush(pushIden)
				except Exception as ex:
					BFun.ezLog('Message (%s) broke command finder in PuxBulletf. Search for 2832516'%pBody,ex)
		return commandList
