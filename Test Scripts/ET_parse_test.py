import xml.etree.ElementTree as ET
import os
import requests

KEYGEN_URL      = '/api/?type=keygen&user='
FIREWALL_IP		= 'REPLACEMEN'
username		= 'REPLACEME'
password 		= 'REPLACEME'

with open('./temp.txt', 'wb') as f:
	f.write(requests.get('https://' + FIREWALL_IP + KEYGEN_URL + username + '&password=' + password, verify=False).content)
	tree = ET.parse('./temp.txt')
	os.remove('./temp.txt')