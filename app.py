import serial
import time
import sys
import wave
from datetime import datetime
import os
#import simpleaudio as sa
import numpy as np
import pygame
from pygame import mixer
import json
import requests
import alsaaudio
from ftplib import FTP
from zipfile import ZipFile

#m = alsaaudio.Mixer('PCM')
m = alsaaudio.Mixer('PCM', cardindex=0)
m.setvolume(0)
pygame.init()
mixer.init(frequency=44100)

version = "1.00.03"
#config
def GetConfig():
    F = open("config.txt")
    data = F.read()
    config = data.split(",")
    return config

def ErrorLog(message):
    try:
        # Specify the URL of the PHP script
        print(message)
        url = "http://apps.tiptonnetworking.com/logs/upload.php"
        # Convert Python dictionary to JSON string
        json_data = json.dumps(message)
        print(json_data)
        # Set headers for JSON data
        headers = {
            "Content-Type": "application/json",
        }
        print("SENDING DATA")
        # Make a POST request to send JSON data
        response = requests.post(url, headers=headers, data=json_data)
        # Print the response from the server
        print(response.text)
        # Close the response to release resources
        response.close()
    except:
        return False

config = GetConfig()
print(config)
# Global Modem Object
modem = serial.Serial()
def read_AT_cmd_response(expected_response="OK"):
    # Set the auto timeout interval
    start_time = datetime.now()
    try:
        while 1:
            # Read Modem Data on Serial Rx Pin
            modem_response = modem.readline()
            print(modem_response)
            print (expected_response+" == "+modem_response.decode('UTF-8').strip()+":")
            # Recieved expected Response
            if "OK" == modem_response.decode('UTF-8').strip() or "CONNECT" == modem_response.decode('UTF-8').strip():
                print("Got expected response")
                return True
            # Failed to execute the command successfully
            elif "ERROR" in modem_response.decode('UTF-8'):
                return False
            # Timeout
            elif (datetime.now()-start_time).seconds > int(config[1]):
                return False

    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print ("Error in read_modem_response function...",str(E))
        return False
        
def exec_AT_cmd(modem_AT_cmd, expected_response="OK"):
    try:
        # Send command to the Modem
        modem.write((modem_AT_cmd + "\r").encode())
        # Read Modem response
        execution_status = read_AT_cmd_response(expected_response)
        print("execution_status: ",execution_status)
        return execution_status

    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print ("Error: Failed to execute the command",E)
        return False

def set_COM_port_settings(com_port):
    modem.port = com_port
    modem.baudrate = 57600 #9600 #115200
    modem.bytesize = serial.EIGHTBITS #number of bits per bytes
    modem.parity = serial.PARITY_NONE #set parity check: no parity
    modem.stopbits = serial.STOPBITS_ONE #number of stop bits
    modem.timeout = 1            #non-block read
    modem.xonxoff = False     #disable software flow control
    modem.rtscts = False     #disable hardware (RTS/CTS) flow control
    modem.dsrdtr = False      #disable hardware (DSR/DTR) flow control
    modem.writeTimeout = 2     #timeout for write
    modem.open()

#initialize
def init_modem_settings():
    # Initialize the Modem
    try:
        # Flush any existing input output data from the buffers
        modem.flushInput()
        modem.flushOutput()
        try:
            # Test Modem connection, using basic AT command.
            modem.write(("AT" + "\r").encode())
        except Exception as E:
            print("ERROR initializing the modem", str(E))

        try:
            # Voice mode
            modem.write(("AT+FCLASS=8" + "\r").encode())
        except Exception as E:
            print("ERROR setting voice mode", str(E))

        # Flush any existing input output data from the buffers
        modem.flushInput()
        modem.flushOutput()

    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print("Error: unable to Initialize the Modem", E, config[3])
        sys.exit()

def close_modem_port():
    # Close the Serial COM Port
    try:
        if modem.isOpen():
            modem.close()
            print("Serial Port closed...")
    except:
        print("Error: Unable to close the Serial Port.")
        sys.exit()

def EnterPin():
    print ("Play EnterPin Msg - Start")
    # Voice mode
    modem.write(("AT+FCLASS=8" + "\r").encode())
    # Set speaker volume to normal
    modem.write(("AT+VGT=128" + "\r").encode())
    # Compression Method: 8-bit linear / Sampling Rate: 8000MHz
    modem.write(("AT+VSM=128,8000" + "\r").encode())
    # Disables silence detection (Value: 0)
    modem.write(("AT+VSD=128,0" + "\r").encode())
    # Put modem into TAD Mode
    modem.write(("AT+VLS=1" + "\r").encode())
    #transmit mode
    modem.write(("AT+VTX" + "\r").encode())
    time.sleep(1)
    # Play Audio File
    wf = wave.open("EnterPin.wav",'rb')
    chunk = 1024
    data = wf.readframes(chunk)
    while data != b'':
        #print(data)
        modem.write(data)
        data = wf.readframes(chunk)
        # You may need to change this sleep interval to smooth-out the audio
        time.sleep(.12)
    wf.close()
    cmd = "<DLE><ETX>" + "\r"
    modem.write(cmd.encode())

    print ("Play EnterPin Msg - END")
    init_modem_settings()
    time.sleep(1)
    CheckPin()
    return

def PinAccepted():
    print ("Play PinAccepted Msg - Start")
    # Voice mode
    modem.write(("AT+FCLASS=8" + "\r").encode())
    # Set speaker volume to normal
    modem.write(("AT+VGT=128" + "\r").encode())
    # Compression Method: 8-bit linear / Sampling Rate: 8000MHz
    modem.write(("AT+VSM=128,8000" + "\r").encode())
    # Disables silence detection (Value: 0)
    modem.write(("AT+VSD=128,0" + "\r").encode())
    # Put modem into TAD Mode
    modem.write(("AT+VLS=1" + "\r").encode())
    #transmit mode
    modem.write(("AT+VTX" + "\r").encode())
    time.sleep(1)
    # Play Audio File
    wf = wave.open("PinAccepted.wav",'rb')
    chunk = 1024
    data = wf.readframes(chunk)
    while data != b'':
        #print(data)
        modem.write(data)
        data = wf.readframes(chunk)
        # You may need to change this sleep interval to smooth-out the audio
        time.sleep(.12)
    wf.close()
    cmd = "<DLE><ETX>" + "\r"
    modem.write(cmd.encode())
    print ("Play PinAccepted Msg - END")
    #modem.write(("AT+VTS=[933,900,100]" + "\r").encode())
    print("Initializing the modem")
    init_modem_settings()
    time.sleep(.5)
    PlayAudio()
    return

def PinWrong():
    print ("Play Audio Msg - Start")
    # Voice mode
    modem.write(("AT+FCLASS=8" + "\r").encode())
    # Set speaker volume to normal
    modem.write(("AT+VGT=128" + "\r").encode())
    # Compression Method: 8-bit linear / Sampling Rate: 8000MHz
    modem.write(("AT+VSM=128,8000" + "\r").encode())
    # Disables silence detection (Value: 0)
    modem.write(("AT+VSD=128,0" + "\r").encode())
    # Put modem into TAD Mode
    modem.write(("AT+VLS=1" + "\r").encode())
    #transmit mode
    modem.write(("AT+VTX" + "\r").encode())
    time.sleep(1)
    # Play Audio File
    wf = wave.open("PinWrong.wav",'rb')
    chunk = 1024
    data = wf.readframes(chunk)
    while data != b'':
        #print(data)
        modem.write(data)
        data = wf.readframes(chunk)
        # You may need to change this sleep interval to smooth-out the audio
        time.sleep(.12)
    wf.close()
    cmd = "<DLE><ETX>" + "\r"
    modem.write(cmd.encode())
    # 2 Min Time Out
    timeout = time.time() + 20
    while 1:
        modem_data = modem.readline()
        #print(modem_data,timeout)
        if "OK" in modem_data.decode("UTF-8"):
            break
        if time.time() > timeout:
            break

    print ("Play Audio Msg - END")
    init_modem_settings()
    time.sleep(1)
    EnterPin()
    return

def delete_files_in_directory(directory_path):
   try:
     files = os.listdir(directory_path)
     for file in files:
       file_path = os.path.join(directory_path, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     print("All files deleted successfully.")
   except OSError:
     print("Error occurred while deleting files.")

def PlayIt(filename):
    print("PLAY AUDIO")
    m.setvolume(100)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    
def record(filename,audio_frames):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(1)
    wf.setframerate(8000)
    wf.writeframes(b''.join(audio_frames))
    wf.close()
    #time.sleep(.1)
    PlayIt(filename)

def PlayAudio():
    print(" !!!!!!!!!!!!!!!! Setting up the modem !!!!!!!!!!!!!!!!!!!!!!!! ")
    # Enter Voice Mode
    print("Enter Voice Mode")
    if not exec_AT_cmd("AT+FCLASS=8","OK"):
        print ("Error: Failed to put modem into voice mode.")
        return

    # Set speaker volume to normal
    print("Set speaker volume to normal")
    if not exec_AT_cmd("AT+VGT=128","OK"):
        print ("Error: Failed to set speaker volume to normal.")
        return

    # Compression Method and Sampling Rate Specifications
    # Compression Method: 8-bit linear / Sampling Rate: 8000MHz
    print("Setting compression")
    if not exec_AT_cmd("AT+VSM=128,8000","OK"):
        print ("Error: Failed to set compression method and sampling rate specifications.")
        return

    # Disables silence detection (Value: 0)
    print("Disables silence detection")
    if not exec_AT_cmd("AT+VSD=128,0","OK"):
        print ("Error: Failed to disable silence detection.")
        return

    # Put modem into TAD Mode
    print("Put modem into TAD Mode")
    if not exec_AT_cmd("AT+VLS=1","OK"):
        print ("Error: Unable put modem into TAD mode.")
        return

    # Enable silence detection.
    # Select normal silence detection sensitivity 
    # and a silence detection interval of 5 s. 
    print("Enable silence detection.")
    if not exec_AT_cmd("AT+VSD=128,50","OK"):
        print ("Error: Failed tp enable silence detection.")
        return

    # Play beep.
    print("!!!!! BEEP !!!!!!")
    if not exec_AT_cmd("AT+VTS=[933,900,100]","OK"):
        print ("Error: Failed to play 1.2 second beep.")
        #return
    
    # Select voice receive mode
        print("Select voice receive mode")
    if not exec_AT_cmd("AT+VRX","CONNECT"):
        print ("Error: Unable put modem into voice receive mode.")
        return
    
    print("STREAM AUDIO")
    audio_frames = []
    C = 0
    FC = 0
    while 1:
        # Read audio data from the Modem
        audio_data = modem.read(1024)
        #print(audio_data)
        audio_frames.append(audio_data)
        #print("audio_frames",audio_frames)
        if audio_data == b'':
            print("No audio received")

        # Check for busy tone is in the stream
        if ((chr(16)+chr(98)).encode() in audio_data):
            print ("Busy Tone... Call will be disconnected.")
            break
    
        # Check if silence is in the stream
        if ((chr(16)+chr(115)).encode() in audio_data):
            print ("Silence Detected... Call will be disconnected.")
            break

        # Check if <DLE><ETX> is in the stream
        if (("<DLE><ETX>").encode() in audio_data):
            print ("<DLE><ETX> Char Recieved... Call will be disconnected.")
            break

        if C >= 10:
            filename = os.getcwd()+"/sound/"+str(FC)+".wav"
            print(filename)
            record(filename,audio_frames)
            audio_frames = []
            FC+=1
            C = 0
        #time.sleep(.1)
        C+=1
    #time.sleep(.5)
    modem.write(("ATH" + "\r").encode())
    delete_files_in_directory("/home/system/AnnounceIt/sound")
    print("Stream Audio Msg - End")
    close_modem_port()
    time.sleep(.5)
    print("Initializing com port")
    set_COM_port_settings(config[3])
    time.sleep(.5)
    print("Initializing the modem")
    init_modem_settings()
    time.sleep(.5)
    read_data()

# check PIN
def CheckPin():
    timeout = time.time() + 10
    while 1:
        print("READING PIN")
        modem_data = modem.readline()
        print("modem_data raw: ", modem_data)
        modem_data = modem_data.decode('UTF-8')
        print("modem_data: ", modem_data)
        P = modem_data.split("")
        print(P)
        emp_str = ""
        x = 4
        for m in P:
            if x > 7: break
            if m.isdigit() and m == config[x]:
                print(config[x],m)
                emp_str = emp_str + m
                x += 1
                time.sleep(.6)
        if "0042" in emp_str:
            print("pin accepted")
            print("PLay accepted message")
            time.sleep(.5)
            PinAccepted()
            break
        else:
            print("WAITING FOR CORRECT PIN")
        if time.time() > timeout:
            EnterPin()
            break

def getupdate(FileName):
    global message
    url = 'http://apps.tiptonnetworking.com/downloads/AnnounceIt/'+FileName
    # Downloading the file by sending the request to the URL
    req = requests.get(url)
    # Split URL to get the file name
    filename = url.split('/')[-1]
    #print(filename)
    # Writing the file to the local file system
    with open(filename,'wb') as output_file:
        output_file.write(req.content)
    print('Download Completed')
    # Re-open the newly-created file with ZipFile()
    zf = ZipFile(filename)
    # Extract its contents into <extraction_path>
    # note that extractall will automatically create the path
    print("Extracting file: ",FileName)
    try:
        zf.extractall()
        # close the ZipFile instance
        zf.close()
        f = filename.split("_")
        f = f[1].replace(".zip","")
        print(f)
        #Delete the downloaded file and reboot
        os.system("rm /home/system/AnnounceIt/"+filename+" &")
        print("Rebooting Now")
        time.sleep(1)
        os.system("sudo reboot")
    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!","GetUpdate Exception: "+str(E),"!!!!!!!!!!!!!!!!!!!")
        return False
    return True

UpdateFile = False
def CheckUpdate():
    global message,NextVersion,UpdateFile
    appversion = version
    update = False
    CV = appversion.split('.')
    CurrentVersion = "AnnounceIt_"+str(CV[0])+"."+str(CV[1])+"."+str(CV[2])
    print(CurrentVersion)
    try:
        ftp = FTP('ftp.tiptonnetworking.com','apps@tiptonnetworking.com','Kh@^gc!m-,r;')
        try:
            ftp.login()
        except Exception as E:
            print(E)
            #return False
        
        ftp.cwd('downloads/AnnounceIt/') 
        entries = ftp.nlst()
        ftp.quit()
        for entry in sorted(entries):
            #Break down the file name to get the version
            if len(entry) > 2:
                A = entry.split("_")
                #print(A)
                B = A[1].split(".")
                #print(B)
                NextVersion = "AnnounceIt"+str(B[0])+"."+str(B[1])+"."+str(B[2])
                if NextVersion == CurrentVersion: 
                    update = False
                else:
                    print("############### UPDATE #############")
                    update = True    
                print("NextVersion: ",NextVersion,entry)
                UpdateFile = entry
        print(UpdateFile,update)
    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!","CheckUpdate Exception: !!!!!!!!!!!!!!!!!!!")
        print(str(E))
    if update:
        return UpdateFile
    else:
        UpdateFile = False
        return False

# listen for ring
BootCounter = 0
def read_data():
    global BootCounter
    m.setvolume(0)
    try:
        while 1:
            print("READING DATA")
            modem_data = modem.readline()
            print("modem_data raw: ", modem_data)
            modem_data = modem_data.decode('UTF-8')
            print("modem_data: ", modem_data)
            if "R" in modem_data:
                # Lets make sure we are in voice mode
                modem.write(("AT+FCLASS=8" + "\r").encode())
                print("RINGING")
                print("Answering")
                modem.write(("ATA" + "\r").encode())
                time.sleep(0.3)
                EnterPin()
                break
            BootCounter += 1
            print("BootCounter:",BootCounter)
            if BootCounter > 28800:  # ~ 8 hours 28800 seconds
                update = CheckUpdate()
                if update:
                    print("Update available")
                    getupdate(update)

                BootCounter = 0
                print("Rebooting Now")
                time.sleep(1)
                os.system("sudo reboot")

    except Exception as E:
        ErrorLog({"time":str(datetime.now()),"device": "AnnounceIt", "message": str(E)})
        print(str(E))
        pass


update = CheckUpdate()
if update:
    print("Update available")
    getupdate(update)

print("Initializing com port")
set_COM_port_settings(config[3])
time.sleep(1)
print("Initializing the modem")
init_modem_settings()
read_data()
