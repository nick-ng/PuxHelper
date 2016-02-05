import PuxGlobal
import BFun
import PuxThreads
from PuxBulletf import PuxBullet
from PuxShowf import PuxShow
import json
import operator
import time
import math
import threading
import os

programRunTic = BFun.tic()
ppBullet = PuxBullet(sendOnly=True)
# Just make sure the lg
BFun.ezLog('Program started at %0.1f'%programRunTic)
# Make the threads
threadList = []
threadList.append(PuxThreads.TorrentT())
threadList.append(PuxThreads.PushBulletT())
# Start the threads
for n in range(len(threadList)):
	print('Starting thread %d'%n)
	threadList[n].start()

# Program is basically over now.
for oneThread in threadList:
	# Wait until each thread joins (finishes)
	oneThread.join()
# Perform program end things.
runTimeString = BFun.toc2Str(programRunTic)
programEndTic = BFun.tic()
BFun.ezLog('Program ended at %0.1f. Ran for %s'%(programEndTic,runTimeString))
ppBullet.sendBrowsers(None,'Program ended at %0.1f. Ran for %s'%(programEndTic,runTimeString))
print('All Done!')
os.system('sudo reboot')
