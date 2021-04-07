from packaging import version
import os
import urllib3
import xml.etree.ElementTree as ET
import getpass
import time
import sys

# Ignore warnings due to the use of verify=False in requests.get calls
import warnings
warnings.filterwarnings("ignore")

# URL constants
OS_VER_URL      		= '/api/?type=op&cmd=<show><system><info></info></system></show>&key='
KEYGEN_URL      		= '/api/?type=keygen&user='
CONFIG_BACKUP_URL_1		= '/api/?type=op&cmd=<save><config><to>'
CONFIG_BACKUP_URL_2		= '</to></config></save>&key='
CONFIG_EXPORT_URL_1		= '/api/?type=op&cmd=<show><config><saved>'
CONFIG_EXPORT_URL_2		= '</saved></config></show>&key='

# Script local path
dir_path = os.path.dirname(os.path.realpath(__file__))

class Unbuffered(object):
    def __init__(self,stream):
        self.stream = stream
    def write(self,datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

# Make sure python doesn't try to buffer output and pushes it to STDOUT immediately
sys.stdout = Unbuffered(sys.stdout)

def pause():
    input("Press any key to continue...")

FIREWALL_IP = input('Please enter the IP address of the firewall to be backed up: ')

# Define the request variable to be used for REST API calls
# cert_reqs='CERT_NONE' and assert_hostname=False ignores errors caused by self-signed certificates
request = urllib3.HTTPSConnectionPool(FIREWALL_IP, cert_reqs='CERT_NONE',assert_hostname=False)

admin = input('Please enter superuser username: ')
password = getpass.getpass('Please enter superuser password: ')

# Request API key from firewall for API user
print('Retrieving API key')
response = request.request('GET', KEYGEN_URL + admin + '&password=' + password)
password = ""

# Parse XML response and extract API key
output = ET.fromstring(response.data)
api_key = output.find('result/key').text

# Saving configuration to firewall
cfg_name = input("Enter configuration name (file.xml): ")
print('\nSaving config to firewall using name: ' + cfg_name)
response = request.request('GET', CONFIG_BACKUP_URL_1 + cfg_name + CONFIG_BACKUP_URL_2 + api_key)

output = ET.fromstring(response.data)
result = output.find('result').text

if result.find('saved') == '-1':
	print('Saving configuration to the firewall failed. Debug output is below. Script aborting')
	quit(1)

# Exporting configuration to file on local machine
print('\nExporting config to ' + dir_path + '/Config_' + FIREWALL_IP + '.xml')

response = request.request('GET', CONFIG_EXPORT_URL_1 + cfg_name + CONFIG_EXPORT_URL_2 + api_key)
open('Config_' + FIREWALL_IP + '.xml', 'wb').write(response.data)