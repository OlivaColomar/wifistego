import subprocess
import time
import os
from datetime import datetime
import codecs
import hashlib
import binascii
import sys

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
	
def check_channel(SSID):
        
	os.system("netsh interface set interface name=\"Wi-Fi\" admin=disable")
	print("DOWN")
	os.system("netsh interface set interface name=\"Wi-Fi\" admin=enable")
	print("UP")
	output = subprocess.check_output("netsh wlan show networks bssid", shell=True)
	s = output.decode(errors='ignore')

	index1 = s.find(SSID)

	##Split until SSID from monitored Wi-Fi
	#print(s[index1:])
	d1 = s[index1:]
	
	##Split from channel until basic rates of speed
	index2 = d1.find("Channel")
	index3 = d1.find("Basic rates")
	d2 = d1[index2:index3]

	##Split until after ":"
	index4 = d2.find(":")
	d3 = d2[index4+2:]
	channel = d3[:d3.find(" ")]
	print(d3)
	print("Channel --> " + channel)
	return channel

def decodeMessage(inputChannels, inputTimes):
		
	channelsInfo = {1: "01", 2: "10", 3: "11", 4: "00", 5: "01", 6: "10", 7: "11", 8: "00", 9: "r", 10: "r", 11: "r", 12: "r", 13: "aux"}
	redundancy = {1: "0", 2: "0", 3: "0", 4: "1", 5: "1", 6: "1", 7: "1", 8: "0", 9: "0", 10: "1", 11: "0", 12: "1", 13: "aux"}
	times = {10: "00", 20: "01", 30: "10", 40: "11", 50: "Error"}
	inverseTimes = {"00": 10, "01": 20, "10": 30, "11": 40}
	message = ""
	
	
	currentChannel = ""
	checkChannel = True
	
	timeInfo = ""
	timeAfter = ""
	timeBefore = ""
	checkTime = True
	
	checkRedBit = False
	criticalTimeFailure = False
	
	##Loop to decode bits exfiltrated
	for i in range(len(inputChannels)-2):
	
		##Check channel
		x = inputChannels[i]
		if(channelsInfo[inputChannels[i]]!="r"): ##Repeated channel
			currentChannel = channelsInfo[inputChannels[i]]
		
		##CheckTime
		if i==0:
			timeInfo = times[inputTimes[0]]
		elif i<len(inputTimes):
			timeAfter = times[inputTimes[i]]
			timeBefore = times[inputTimes[i-1]]
			if(timeAfter == "Error" or timeBefore == "Error"):
				timeInfo == "Error"
			else:
				timeInfo = xor(timeAfter,timeBefore)
		else:##Array of times is shorter than the one from channels, when the channel is 13 it just indicate the end of exfiltration process #TBD
			timeInfo = "noTime"
			
		print("Time")
		print(timeInfo)
		
		
		##Get message
		##In the last check the strings won't be the same never, then the message will maintain the same
		if(currentChannel == timeInfo):
			message = message + currentChannel
			criticalTimeFailure = False
		elif(currentChannel == "aux" and i<len(inputTimes)-1): ## Channel 13 introduced incorrectly during the exfiltration. But if it is introduced in the last channel of information transmitted won't be detected.
			if(xor(timeInfo[0],timeInfo[1])==redundancy[inputChannels[i+1]]): ##Check redundancy bit with timeInfo
				print("Wrong channel information -> TimeInfo redundancy bit is correct")
				message = message + timeInfo
				criticalTimeFailure = False
			else: ##Unknown exfiltrated bits
				print("Unknown information --> Error Detected")
				message = message + "xx"
		else:
			
			if(i<len(inputTimes)-1 and i>0):
				if(xor(currentChannel[0],currentChannel[1])==redundancy[inputChannels[i+1]]): ##Check redundancy bit with channels
					print("Wrong time information -> Channel redundancy bit is correct A")
					message = message + currentChannel
					## Correct the channel to not drag the error. This correction has not been implemented in the last channel information case because is useless
					if(not(criticalTimeFailure)): #Especial case when the first time is incorrect, cannot be corrected next errors until there is a time correct
						correctedTime = xor(currentChannel,timeBefore)
						print("Corrected time to -> " + correctedTime)
						inputTimes[i] = inverseTimes[correctedTime]
				elif((xor(timeInfo[0],timeInfo[1])==redundancy[inputChannels[i+1]]) and timeInfo != "Error"): ##Check redundancy bit with timeInfo, except when the time is too long (in that case the information can't be corrected)
					print("Wrong channel information -> TimeInfo redundancy bit is correct")
					message = message + timeInfo
					criticalTimeFailure = False
				else: ##Unknown exfiltrated bits
					print("Unknown information --> Error Detected")
					message = message + "xx"
			elif(i==len(inputTimes)-1):
				if(xor(currentChannel[0],currentChannel[1])==redundancy[inputChannels[i+2]]): ##Check redundancy bit with channels
					print("Wrong time information -> Channel redundancy bit is correct B")
					message = message + currentChannel
				elif((xor(timeInfo[0],timeInfo[1])==redundancy[inputChannels[i+2]]) and timeInfo != "Error"): ##Check redundancy bit with timeInfo, except when the time is too long (can't be corrected)
					print("Wrong channel information -> TimeInfo redundancy bit is correct")
					message = message + timeInfo
				else: ##Unknown exfiltrated bits
					print("Unknown information --> Error Detected")
					message = message + "xx"
			else:##First information, we do not have two times to do XOR confirmation
				 ##!!¡¡ If there has been a wrong time in the first channel information then, the correction of the time cannot be execute in the second channel (unless this will cause problems onward)
				print(timeInfo)
				if(timeInfo != "Error"):
					if(xor(currentChannel[0],currentChannel[1])==redundancy[inputChannels[i+1]]): ##Check redundancy bit with channels
						print("Wrong time information -> Channel redundancy bit is correct")
						message = message + currentChannel
						criticalTimeFailure = True
						## The correction of the time cannot be done in this case, there is no time before this one to do the xor operation
					else: ##Unknown exfiltrated bits
						print("Unknown information --> Error Detected")
						message = message + "xx"
				else: ##Unknown exfiltrated bits, because of too long time
						print("Unknown information (time invalid) --> Error Detected")
						message = message + "xx"
					
	
		print("Message = " + message)
	
	##LOOP
	print()
	print("CORRECTED CHANNELS AND TIMES")
	print(inputChannels)
	print(inputTimes)
	
	return message
	
##Monitoring channel expecting for data method
def lookingForData(bssid):
	print("WAITING FOR DATA")
	print()
	waitingForData = True
	channel = 0
	time1 = 0
	interval_Time = 0.5
	
	channel = check_channel(bssid)
	
	while waitingForData:
		
		##Monitor channel
		channel = check_channel(bssid)

		##Check if it's different from 13
		if(channel != "13" and channel != ""):
			time1 = round(datetime.timestamp(datetime.now()))
			waitingForData = False
		
	return [time1,channel]

def exfiltratingInfo(bssid,firstTime, firstChannel):
	print("START DATA EXFILTRATION")
	print()
	##Receiving data method##(input time --> time1=time)
	inChannels = [int(firstChannel)]
	inTimes = []
	monitoringChannel = True
	check_Interval_Time = 0.5
	monitoredChannel = 0
	lastChannel = firstChannel ##It must have the same value as monitoredChannel to not save the time=0
	monitoredChannel = firstChannel
	time1 = 0
	time2 = firstTime
	t = 0
	timeCodes = [10,20,30,40,50]
	timeEncoded = 0

	#LOOP THAT CHECKS THE CHANNEL ONCE THE TRANSMISSION STARTED
	while monitoringChannel:
		#Obtain actual channel
		monitoredChannel = check_channel(bssid)
		#print("Channel = " + monitoredChannel + ". Last Channel = " + lastChannel)
	
		#Check if it is 13 the Channel (Beginning)
		if(monitoredChannel == "13" and lastChannel != "13"):##EL CONTENIDO DE ESTE IF ES EXACTAMENTE IGUAL AL DE DATA EXFILTRATING CUANDO NO COINCIDEN LOS CANALES, PODRÍA HACERSE UN MÉTODO
			#Obtain timestamp
			time2 = round(datetime.timestamp(datetime.now()))
			#Substract time1 to time2 (t=time2-time1)
			t = time2 - time1
			
			#Obtain realEncodedTime
			for i in range (0,len(timeCodes)):
				if((timeCodes[i] - 4) <= t and (timeCodes[i] + 4 >= t)):
					timeEncoded = timeCodes[i]
					break ##Break needed to avio entering the elif condition in the last rotation of the loop
				elif(timeCodes[len(timeCodes)-1]-4 < timeCodes[i]): ## When it is more than 44s
					timeEncoded = timeCodes[i]		
			print("Channel= " + str(monitoredChannel) + ". Time= " + str(timeEncoded))
			inChannels.append(int(monitoredChannel))
			inTimes.append(timeEncoded)
		elif(monitoredChannel != "13" and lastChannel == "13" and monitoredChannel != ""): #END OF DATA EXFILTRATION
			##The last channel 13 can be wrong, then let's check the t=time2-time1, if it is bigger than t4+4 the transmission has ended.
			##But if it isn't the end, it must be considered as a wrong channel the last 13 and must be correct
			time2 = round(datetime.timestamp(datetime.now()))
			t = time2 - time1
			
			if(t > timeCodes[len(timeCodes)-2] + 4):
				inChannels.append(int(monitoredChannel))
				monitoringChannel = False
			else:
				#Obtain timestamp
				time2 = round(datetime.timestamp(datetime.now()))
				#Substract time1 to time2 (t=time2-time1)
				t = time2 - time1

				#Obtain realEncodedTime
				for i in range (0,len(timeCodes)):
					if((timeCodes[i] - 4) <= t and (timeCodes[i] + 4 >= t)):
						timeEncoded = timeCodes[i]

						print("Channel= " + str(monitoredChannel) + ". Time= " + str(timeEncoded))
				inChannels.append(int(monitoredChannel))
				inTimes.append(timeEncoded)
		elif(monitoredChannel != ""):##DATA EXFILTRATING // Second condition necessary when there is a channel 13 introduced into the message
			#Compare last channel and actual channel

			if(monitoredChannel != lastChannel):
				#Obtain timestamp
				time2 = round(datetime.timestamp(datetime.now()))
				#Substract time1 to time2 (t=time2-time1)
				t = time2 - time1

				#Obtain realEncodedTime
				for i in range (0,len(timeCodes)):
					if((timeCodes[i] - 4) <= t and (timeCodes[i] + 4 >= t)):
						timeEncoded = timeCodes[i]
						break ##Break needed to avio entering the elif condition in the last rotation of the loop
					elif(timeCodes[len(timeCodes)-1]-4 < timeCodes[i]): ## When it is more than 44s
						timeEncoded = timeCodes[i]
						
				print("Channel= " + str(monitoredChannel) + ". Time= " + str(timeEncoded))
				inChannels.append(int(monitoredChannel))
				inTimes.append(timeEncoded)
	
		#Update parameters
		time1 = time2
		print(inChannels)
		print(inTimes)
		
		##To avoid errors when no channel is detected (it can happen when the channel is changing)
		if(monitoredChannel != ""):
			lastChannel = monitoredChannel
		
	return [inChannels,inTimes]

def obtainOriginalInfo(decodedMessage,bssid):
	print(decodedMessage)

	binary = lambda x: " ".join(reversed( [i+j for i,j in zip( *[ ["{0:04b}".format(int(c,16)) for c in reversed("0"+x)][n::2] for n in [1,0] ] ) ] ))
	m = hashlib.md5()
	m.update(bssid.encode('utf-8'))
	key = m.hexdigest()
	binarykey = binary(key).replace(" ","")
	
	##OBTAIN BINARY DATA FROM XOR(key,infoEncoded)
	binarydata = int("0b"+ xor(binarykey,decodedMessage),2)
	##BINARY TO STRING
	informationExfiltrated = binascii.unhexlify('%x' % binarydata).decode("utf-8")
	
	return informationExfiltrated
	
	
## MAIN	
	
bssid = sys.argv[1] ##SSID passed by parameter

while (True):
	
	firstInfo = lookingForData(bssid)

	exfiltratedInfo = exfiltratingInfo(bssid,firstInfo[0], firstInfo[1])

	print("Exfiltration results: ")
	print("CHANNELS")
	print(exfiltratedInfo[0])
	print("TIMES")
	print(exfiltratedInfo[1])	
	print()
	print("ExfiltratedInfo DECODED BITS")
	decodedMessage = decodeMessage(exfiltratedInfo[0], exfiltratedInfo[1])
	print(decodedMessage)
	information = obtainOriginalInfo(decodedMessage,bssid)
	print("INFORMATION EXFILTRATED --> " + information)