"""
Server program

How To Run
------------

python3 Server.py -p <a port number>

E.g. 
python3 Server.py -p 1234                       # server listen to port 1234

Dependencies:
 - socket
 - json
 - pandas
 - datetime
 - matplotlib
 - numpy
 - cryptography
"""

import socket
import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# initialize the AES decryptor
def AES_init(num):
    # create a known key and initialization vector for aes
    key = num.to_bytes(32)
    iv = num.to_bytes(16)

    # create AES cipher and decrypter using cyptography module
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    # also create a padder to ensure messages are the correct length
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

    return decryptor, unpadder

# decrypt the message with AES
def AES_dec(data, decryptor, unpadder):
    # decrypt the message using the created cipher
    data_decrypted = decryptor.update(data) + decryptor.finalize()
    # remove padding from the decrypted message
    data_unpadded = unpadder.update(data_decrypted) + unpadder.finalize()
    data_decoded = data_unpadded.decode('utf-8')

    return data_decoded

# initialize TCP socket connection
def socket_init(port):
    # create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind to input port
    s.bind(('', port))
    # put at most 2 connections in backlog (or say 3 connections at most). Refuse more connections
    s.listen(2)
    return s

# update the website's database file
def update_dbs(rmsg):
    # load database csv to pandas
    dbs = pd.read_csv('./inventory-app/data/inventory.csv', header=None, names=['id','mass','price','total','count','timestamp'])
    
    # add or replace entry as needed
    idx = dbs.index[dbs['id'] == rmsg['id']]
    
    dbs.loc[idx, 'id'] = rmsg['id']
    dbs.loc[idx, 'total'] = round(rmsg['mass'], 2)
    dbs.loc[idx, 'count'] = rmsg['count']
    dbs.loc[idx, 'timestamp'] = rmsg['timestamp']

    # save updates to csv
    dbs.to_csv('./inventory-app/data/inventory.csv', header=False, index=False)
    del dbs

# update the history json file with the latest data 
def update_history(rmsg):
    # load in existing history
    json_file = open('./inventory-app/data/history.json', 'r')
    history = json.load(json_file)
    json_file.close()
    
    # add most recentdata for the item
    try:
        history[rmsg['id']]["timestamps"].append(rmsg['timestamp'])
        history[rmsg['id']]["counts"].append(rmsg['count'])
    except Exception:
        history[rmsg['id']] = {"timestamps": [rmsg['timestamp']], "counts": [rmsg['count']]}
        
    # write back to json file
    json_file = open('./inventory-app/data/history.json', 'w')
    json.dump(history, json_file, indent=4)
    json_file.close()
    
    return history

# predict when the item will run out based on recent data history
def predict(timestamps, counts):
    # initialize most recent datapoint of valid
    r_counts = counts[::-1]
    r_timestamps = timestamps[::-1]
    i = 0
    valid_timestamps = [int(datetime.timestamp(datetime.strptime(r_timestamps[0], "%Y-%m-%d %H:%M:%S")))]
    valid_counts = [r_counts[0]]
    
    # use recent values up until the last peak
    while i < len(timestamps)-1:
        if r_counts[i] < r_counts[i+1]:
            valid_timestamps.append(int(datetime.timestamp(datetime.strptime(r_timestamps[i+1], "%Y-%m-%d %H:%M:%S"))))
            valid_counts.append(r_counts[i+1])
        else:
            break
        i += 1
    if (len(valid_timestamps) <= 1):
        return None
    
    # calculate the prediction using linear regression
    v_t = np.array(valid_timestamps[::-1])
    v_c = np.array(valid_counts[::-1])
    slope, intercept, _, _, _ = linregress(v_t, v_c)
    x_intercept = int(-intercept / slope)
    zero_time = datetime.fromtimestamp(x_intercept).strftime("%Y-%m-%d %H:%M:%S")
    return zero_time

# generate history plot
def generate_plot(rmsg, history):
    # load data from history
    timestamps = history[rmsg['id']]["timestamps"]
    counts = history[rmsg['id']]["counts"]
    
    # get prediction for running out
    if (counts[-1] != 0):
        zero_time = predict(timestamps, counts)
    else:
        zero_time = timestamps[-1]
    
    # create graph using matplotlib
    plt.plot(timestamps, counts, marker='o', linestyle='-')
    plt.xlabel('Timestamps')
    plt.ylabel('Quantity')
    plt.suptitle('Inventory History for ID: {}'.format(rmsg['id']))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.ylim(0, max(counts) + 1)
    if (zero_time is not None):
        plt.title("{} will run out on: {}".format(rmsg['id'], zero_time), fontsize=10, color='gray')
    plt.savefig('./inventory-app/public/plot.png')

if __name__ == "__main__":
    AES_NUM = 42
    SOCKET_PORT = 1234

    try:
        s = socket_init(SOCKET_PORT)
        
        while True: 
            # create decryption instance
            decrytor, unpadder = AES_init(AES_NUM)
            
            print("="*30)
            print("waiting for connection")
            # Establish connection with client, where c is the connection handler and addr is the client's ip
            c, addr = s.accept()
            print ('Got connection from', addr)

            ## message transmission
            # receive message from the client
            rmsg_bytes = c.recv(1024)
            
            # print("\nEncoded Message: ", rmsg_bytes)
            # message must be decrypted
            rmsg = json.loads(AES_dec(rmsg_bytes, decrytor, unpadder))

            # first part of message is unique client id
            # second part of message is the encrypted message
            # print("Decrypted data:")
            print("id: {}\ttimestamp: {}\tmass (g): {}\tcount: {}".format(
                  rmsg['id'], rmsg['timestamp'], rmsg['mass'], rmsg['count']))
            
            update_dbs(rmsg)

            history = update_history(rmsg)
            
            generate_plot(rmsg, history)
            
            

            c.close() 

    except ConnectionRefusedError:
        print("Connection refused. You need to run server program first.")
    finally: # must have
        print("free socket")
        s.close()
    
    print("end")
