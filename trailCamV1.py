#!/usr/bin/python3
#
# Raspberry Pi TrailCam Version 1
#
# Author: Jean-Claude Graf
# Date  : 04/03/2017

#-#-#-#-#---Import---#-#-#-#-#

import RPi.GPIO as GPIO
import picamera
import time
import os
import shutil
import json


#-#-#-#-#---Setting for camera---#-#-#-#-#

with open('config.json', 'r') as f:
    config = json.load(f)


#-#-#-#-#---Setting for camera---#-#-#-#-#

camera = picamera.PiCamera()
camera.sharpness = 0
camera.contrast = 0
camera.brightness = 50
camera.saturation = 0
camera.iso = 0
camera.video_stabilization = False
camera.exposure_compensation = 0
camera.exposure_mode = 'auto'
camera.meter_mode = 'average'
camera.awb_mode = 'auto'
camera.image_effect = 'none'
camera.color_effects = None
camera.rotation = 0
camera.hflip = True
camera.vflip = True
#recheck
camera.zoom = (0.0, 0.0, 1.0, 1.0)
#frame, resolution, timestamp
camera.video_denoise = True
camera.led = False

camera.annotate_background = picamera.Color('black')
# camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S')


#-#-#-#-#---Setup GPIO---#-#-#-#-#

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#-PIR Sensor GPIO
sensorGPIO = config['sensorGPIO']
GPIO.setup(sensorGPIO, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

#-Relay GPIO
relayGPIO = config['relayGPIO']
GPIO.setup(relayGPIO, GPIO.OUT)
GPIO.output(relayGPIO, GPIO.LOW)

#TODO: #-Shutdown Battery GPIO
# batteryGPIO = config['batteryGPIO']
# GPIO.setup(batteryGPIO, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

#-Status LED GPIO
ledGPIO = config['ledGPIO']
GPIO.setup(ledGPIO, GPIO.OUT)

#-Status Button GPIO
buttonGPIO = config['buttonGPIO']
GPIO.setup(buttonGPIO, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)


#-#-#-#-#---Global variables---#-#-#-#-#

motionDetected = False

defaultRecordingTime = config['recordingTime']
recordingTimeLeft = defaultRecordingTime

pathToSave = config['path']
largestRecordNumber = 1
nameOfRecord = ""

previousBatteryStatus = False
isShuttingDown = False

isActive = False

isPressfuncRunning = False

firstCall = 0

# Change Time Variables
isEnterTime = False
isReadyToSetTime = False
hourString = ""
minString = ""
isHourSet = False
isMinSet = False


#-#-#-#-#---HandleStatusbutton Pressed---#-#-#-#-#


def statusBtnPressed(channel):

    global isPressfuncRunning
    global isActive
    global isEnterTime
    # global isReadyToSetTime
    # global hourString
    # global minString
    # global isHourSet
    # global isMinSet

    print("Callback called")
    
    index = 0

    changeStatus = 3
    restartScript = 5
    enterTime = 7
    shutdownRPi = 10

    # Set index to the seconds pressed
    while GPIO.input(buttonGPIO) == GPIO.HIGH:

        index += 1

        print("Index is " + str(index))

        if (index == changeStatus or index == restartScript or index == enterTime or index == shutdownRPi) and isEnterTime == False:

            for _ in range(0,5):
                time.sleep(0.1)
                GPIO.output(ledGPIO, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(ledGPIO, GPIO.LOW)
        
            # if index == enterTime:
            #     print("Special index called")
            #     isEnterTime = True
            #     isHourSet = False
            #     isMinSet = False
            #     isReadyToSetTime = False

        else:
            time.sleep(0.5)
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(ledGPIO, GPIO.LOW)


    # Determinde the output for the chosen time
    if isEnterTime == False:
        if index == 0 or index == 1 or index == 2:

            print("Print status")

            if isActive == True:

                print("isActive is True")

                GPIO.output(ledGPIO, GPIO.HIGH)
                time.sleep(1.5)
                GPIO.output(ledGPIO, GPIO.LOW)

            else:

                print("isActive is False")

                for _ in range(0,5):
                    GPIO.output(ledGPIO, GPIO.HIGH)
                    time.sleep(0.1)
                    GPIO.output(ledGPIO, GPIO.LOW)
                    time.sleep(0.1)

        elif index == changeStatus:

            print("Change activ mode")

            if isActive == True:

                isActive = False

                if camera.recording == True:
                    stopRecording() 

                print("isActive is set to False")
                print("Camera is deactivated")

            else:

                isActive = True

                print("isActive is set to True")
                print("Camera is active now")

        elif index == restartScript:

            print("Restart Script")
            os.system('sh /home/pi/Documents/TrailCam/TrailCam-V1/runRestartScript.sh')

        elif index == shutdownRPi:

            shutDown()

    # else:

    #     print("Change time")
    #     print("isReadyToSetTime", isReadyToSetTime)

        # if isReadyToSetTime == True:

        #     index -= 1

        #     if isHourSet == False:

        #         while index >= 24:

        #             index -= 24

        #         hourString = str(index)
        #         print("Hour set to " + hourString)

        #     elif isMinSet == False and isHourSet == True:

        #         index * 60

        #         while index >= 60:

        #             index -= 60

        #         minString = str(index)
        #         print("Mib set to " + minString)
        
        # else:
        #     # isReadyToSetTime = True
        #     print("esle")

        # if isHourSet == True and isMinSet == True:
        #     isEnterTime = False
        #     os.system('sudo date -s "' + hourString + ":" + minString +'"')

GPIO.add_event_detect(buttonGPIO, GPIO.RISING,  callback = statusBtnPressed, bouncetime = 500)
# GPIO.wait_for_edge  (buttonGPIO, GPIO.RISING)


# TODO: #-#-#-#-#---Shutdown the pi when the battery is low---#-#-#-#-#

# def shutDownBatteryLow(channel):

#     global previousBatteryStatus

#     if previousBatteryStatus == False:

#         print("Battery seems to be low, recheck in 1 minute")
#         previousBatteryStatus = True

#         time.sleep(60)

#         if GPIO.input(buttonGPIO) == False:

#             print("Battery is low, will shutdown")

#             shutDown()

#         else:

#             print("Battery was just temporarely low, Pi will continous running")
#     else:

#         previousBatteryStatus = False


# GPIO.add_event_detect(batteryGPIO, GPIO.FALLING,  callback = shutDownBatteryLow)


#-#-#-#-#---Shutdown the pi when the battery is low---#-#-#-#-#

def shutDown():

    global isShuttingDown

    isShuttingDown = True

    print("Preparing to shut down the Pi")

    if camera.recording == True:

        print("Camera is recording")
        stopRecording()

        print("Shutdown in 10 seconds")
        time.sleep(10)

    print("Shutdown!")

    for _ in range(0, 4):

        GPIO.output(ledGPIO, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(ledGPIO, GPIO.LOW)
        time.sleep(0.1)

    GPIO.cleanup()
    os.system('sudo umount /media/usb')
    os.system('sudo shutdown -h now')


#-#-#-#-#---Stop recording---#-#-#-#-#

def stopRecording():

    global recordingTimeLeft
    global largestRecordNumber

    print("Stop Recording")
    print("Record saved with the name " + nameOfRecord + " at " + pathToSave)

    GPIO.output(relayGPIO, GPIO.LOW)

    camera.stop_recording()

    recordingTimeLeft = defaultRecordingTime

    largestRecordNumber += 1


#-#-#-#-#---Stop recording---#-#-#-#-#

def createIndexForName(index):

    indexLength = len(str(index))

    if 4 - indexLength == 3:
        return "000" + str(index)

    elif 4 - indexLength == 2:
        return "00" + str(index)

    elif 4 - indexLength == 1:
        return "0" + str(index)

    else:
        return str(index)


#-#-#-#-#---Figure out the index of the last video ---#-#-#-#-#

for f in os.listdir(pathToSave):

    if f.startswith("Video") == True:

        number = int(f[5:-12])
        
        if number > largestRecordNumber:

            largestRecordNumber = number + 1


#-#-#-#-#---Main loop---#-#-#-#-#

try:

    print("Ready")

    for _ in range(0,5):
        GPIO.output(ledGPIO, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(ledGPIO, GPIO.LOW)
        time.sleep(0.2)

    while True:
        time.sleep(0.1)
        if isShuttingDown == False and isActive == True and not GPIO.input(buttonGPIO) == GPIO.HIGH:
        
            motionDetected = True if GPIO.input(sensorGPIO) == 1 else False
            # print("Motion detected:" , motionDetected)

            #-Start recording
            if motionDetected and not camera.recording:
                
                redordingTimeLeft = defaultRecordingTime

                print("Motion Detected!")
                print("Start recording!")
                
                #-Enable the lamp
                GPIO.output(relayGPIO, GPIO.HIGH)

                indexName = createIndexForName(largestRecordNumber)

                camera.annotate_text = time.strftime('%Y-%m-%d %H:%M:%S')

                nameOfRecord = time.strftime('%Y-%m-%d_%H:%M:%S') +".h264"
                camera.start_recording(pathToSave + nameOfRecord)
                
                
            #-Extend recording time
            elif motionDetected and camera.recording:
                
                print("Motion Detected!")
                print("Continous recording!")
                
                recordingTimeLeft = defaultRecordingTime

            #-Should recording be stopped
            elif camera.recording and not motionDetected:

                #-Stop recording
               if recordingTimeLeft <= 0:
                   
                   stopRecording()

                   print("Ready to detect motion...")

                   time.sleep(1)

                #-Continous recording
               else:
                   
                    print("Recording time left " + str(recordingTimeLeft))
                    recordingTimeLeft -= 1

            #else:

                #print("Waiting for motion")

            #-Determine sleep time
            # if camera.recording:

            #     time.sleep(1)

            # else:

            #     time.sleep(0.5)

            time.sleep(0.5)

            # print("-----------")
            # print("Camera is recording:", camera.recording)
            # print("Recording time left", recordingTimeLeft)
            # print("Motion detected:", motionDetected)
            # print("-----------")

#-Quit when a key is pressed
except KeyboardInterrupt:
    
    if camera.recording:

        stopRecording()

        time.sleep(2)

    print("Quit")
    GPIO.cleanup()





























