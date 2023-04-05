#!/usr/bin/env python3
from base64 import b64encode
from os.path import exists
import sys
import requests
from dotenv import dotenv_values

if exists('.env'):
    config = dotenv_values('.env')
else:
    sys.exit('.env file not found, exiting')

try:
    WSKEY   = config['WSKEY']
    SECRET  = config['SECRET']
    INSTID  = config['INSTID']
except KeyError:
    sys.exit('one or more of the expected variables not found in .env file, exiting')

combo       = WSKEY+':'+SECRET
auth        = combo.encode()
authenc     = b64encode(auth)
authheader  = { 'Authorization' : 'Basic %s' %  authenc.decode() }
url         = "https://oauth.oclc.org/token?grant_type=client_credentials&scope=WorldCatMetadataAPI"

def getToken():

    try:
        r = requests.post(url, headers=authheader)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return r.json()['access_token']

TOKEN = getToken()

def updateLbd(metadatanen, token):

    url = 'https://worldcat.org/lbd/data'

    headers = {'Authorization': f'Bearer {token}',
           'Content-Type': 'application/vnd.oclc.marc21+xml'}

    try:
        update = requests.post(url, headers=headers, data=metadatanew)
        update.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if update.status_code == 401:
            raise ValueError('Token expired')
        else:
            SystemExit(err)

    return update


# take identifiers from stdin
for ocn in sys.stdin:
    # print(ocn)
    with open('meta.xml', 'r') as f:
        metadata = f.read()
        # response = requests.post(url, headers=headers, data=metadata)
        metadatanew = metadata.replace('oclcnum', str(ocn.strip()))    

        try:
            response = updateLbd(metadatanew, TOKEN)
        except ValueError:
            # token has expired, get a fresh token and redo search
            print('getting new token')
            TOKEN = getToken()
            response = updateLbd(metadatanew, TOKEN)


        if response.status_code == 201:
            # Record created successfully
            # responsetext = response.text
            print(f'Created new record with OCLC number: {ocn}')
        else:
            # Record creation failed
            # print(f'Record creation failed with status code {response.status_code}: {response.text}')
            print(f'Record creation failed with status code {response.status_code}: {ocn}')
