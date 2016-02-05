import PuxGlobal
import BFun
import transmissionrpc
import re
import os
import time
try:
	# Web adapters are private
	import NoPubWebAdapters
except ImportError as ex:
	print('Couldn\'t import web adapters. Script may not function properly.')
	NoPubWebAdapters = None
# Functions that deal with the BitTorrent protocol.

# Global Variables
GLOBAL_NUMBER_EXTENSIONS = ['mp4','mp3']

def torrentSearch(searchDict):
	# Check if external web adapters have been imported.
	if NoPubWebAdapters:
		return NoPubWebAdapters.torrentSearch(searchDict)
	else:
		print('No web adapters found. Script may not function properly.')
		return []
	
def connectTransmission():
	# Connects to transmission and starts transmission if not already running.
	# Returns a transmission session object
	try:
		return transmissionrpc.Client()
	except transmissionrpc.error.TransmissionError as ex:
		if 'connection refused' in str(ex).lower():
			print('Starting Transmission')
			# Start transmission and return control to terminal
			os.system('transmission-gtk &')
			print('Transmission Starting')
			unConnected = 1
			# Try to connect to transmission until successful.
			while unConnected > 0:
				try:
					return transmissionrpc.Client()
					#unConnected = 0
				except transmissionrpc.error.TransmissionError as ex:
					print('Failed to connect to Transmission. (%d times)'%unConnected)
					unConnected = unConnected + 1
					time.sleep(1) # Sleep 1 second for sanity.
		else:
			BFun.ezLog('Unexpected error when connecting to transmission. Search for 1435813',ex)
	except Exception as ex:
		BFun.ezLog('Unexpected error when connecting to transmission. Search for 1435813a',ex)
				
def addTorrentURL(someSession,torrentDict):
	# Add torrent by URL
	someURL = torrentDict['URL']
	fileExtension = torrentDict['extension']
	someSession.add_torrent(someURL)
	# Get list of all torrent objects
	torrents = someSession.get_torrents()
	# Get the torrent we just added.
	torrent = torrents[-1]
	# Note: tSess.get_torrent(1) is the same as torrents[0]

	# Get the unique hash of the torrent so working with torrents is easier.
	uniqueHash = torrent.hashString
	fileList = someSession.get_torrent(uniqueHash).files()
	#tSess2.get_torrent(uniqueHash).files()
	filePairs = []
	for m in range(len(fileList)):
		fileName = fileList[m]['name']
		if fileExtension.lower() in fileName.lower():
			BFun.ezPrint('Found %s in %s'%(fileExtension,fileName))
			filePairs.append((m,fileName))
	watchedTorrent = {}
	watchedTorrent['hash'] = uniqueHash
	watchedTorrent['show'] = 'test'
	watchedTorrent['epNum'] = 1
	watchedTorrent['filePairs'] = filePairs # list of (fileNumber,fileName)
	watchedTorrent['URL'] = someURL
	BFun.ezPrint('Added torrent with %s'%filePairs[0][1])
	return watchedTorrent
	

