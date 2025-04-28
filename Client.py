"""
Dependencies:
 - spidev
 - time
 - RPi
 - queue
 - socket
 - json
 - functools
 - datetime
 - cryptography

"""

import spidev               # To communicate with SPI devices
from time import sleep	    # To add delay
import RPi.GPIO as GPIO	    # To use GPIO pins
from queue import Queue     # Keep FIFO data

import socket               # Connect to PC
import json
from functools import partial
import datetime

# import the necessary modules from the cryptography package
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# Read ADC data
def analogInput(channel):
    # create spi connection
    spi.max_speed_hz = 5000000
    spi.mode = 3
    adc = spi.readbytes(2)
    data = (adc[0] << 8) + adc[1]
    return data

# initialize AES encyptor
def AES_init(num):
    # create a known key and initialization vector for aes
    key = num.to_bytes(32)
    iv = num.to_bytes(16)

    # create AES cipher and encrypter using cyptography module
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    # also create a padder to ensure messages are the correct length
    padder = padding.PKCS7(algorithms.AES.block_size).padder()

    return encryptor, padder

# encrypt the message using AES
def AES_enc(data, encryptor, padder):
    # pad and encrypt the message using the created cipher
    data_padded = padder.update(data.encode('utf-8')) + padder.finalize()
    data_encrypted = encryptor.update(data_padded) + encryptor.finalize()
    # print("Encrypted message: ", data_encrypted)

    return data_encrypted

# transmit data over TCP IP socket
def transmit(timestamp, mass, count, ip, port, id):
    encryptor, padder = AES_init(AES_NUM)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        
        msg = {"id": id, "timestamp": timestamp, "mass": mass, "count": count}
        smsg = json.dumps(msg)
        # print("\nSending Data: %s" % smsg)
        s.send(AES_enc(smsg, encryptor, padder))
    except ConnectionRefusedError:
        print("Connection refused. You need to run server program first.")
    finally:
        s.close()


if __name__ == "__main__":
    
    # data acquisition vars
    
    spi = spidev.SpiDev() 
    spi.open(0,0)
    GPIO.setmode(GPIO.BCM)
    # outputs = Queue(3)
    readings = []
    idx = 0
    MASS_PER = 11
    last_count = -1
    
    # transmission/encryption vars
    CLIENT_ID = 'pi_test'
    AES_NUM = 42
    SOCKET_IP = '192.168.1.1'
    SOCKET_PORT = 1234
    print("Trying to connect to %s:%d" % (SOCKET_IP, SOCKET_PORT))
    
    send_data = partial(transmit, ip=SOCKET_IP, port=SOCKET_PORT, id=CLIENT_ID)
    
    while True:
        
        readings.append(analogInput(0)) # Reading from CH
        idx += 1
        if (idx == 20): # Average after 20 reads
            adc_val = sum(readings) / len(readings)
            mass = (adc_val * 0.007131) + 18.82
            if (mass < 23):
                count = 0
            else:
                count = round(mass / MASS_PER)
            print("adc: {}\tmass: {}\tQuantity: {}".format(adc_val, round(mass, 6), count))
            if (count != last_count):
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("\n" + "*"*50)
                print("Quantity changed to {}, sending data at {}".format(count, timestamp))
                print("*"*50 + "\n")
                send_data(timestamp, mass, count)
                last_count = count
            readings.clear()
            idx = 0
            sleep(1) # some delay to prevent multiple reads for the same motion
        sleep(0.05) #values are read every 50ms
