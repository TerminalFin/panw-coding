import requests
import getpass
import time
import sys
from bs4 import BeautifulSoup

# Ignore warnings due to the use of verify=False in requests.get calls
import warnings
warnings.filterwarnings("ignore")

# URL constants
OS_VER_URL      = '/api/?type=op&cmd=<show><system><info></info></system></show>&key='
KEYGEN_URL      = '/api/?type=keygen&user='
CHECK_SW_URL    = '/api/?type=op&cmd=<request><system><software><check></check></software></system></request>&key='
CONTENT_URL     = '/api/?type=op&cmd=<request><content><upgrade><download><latest/></download></upgrade></content></request>&key='
JOB_CHECK_URL   = '/api/?type=op&cmd=<show><jobs><id>'
JOB_CHECK_URL2  = '</id></jobs></show>&key='
CU_INSTALL_URL  = '/api/?type=op&cmd=<request><content><upgrade><install><version>latest</version></install></upgrade></content></request>&key='
PANOS_REQ_URL1  = '/api/?type=op&cmd=<request><system><software><download><version>'
PANOS_REQ_URL2  = '</version></download></software></system></request>&key='
PANOS_UP_URL1   = '/api/?type=op&cmd=<request><system><software><install><version>'
PANOS_UP_URL2   = '</version></install></software></system></request>&key='
REBOOT_URL      = '/api/?type=op&cmd=<request><restart><system></system></restart></request>&key='
versions = []

class Unbuffered(object):
    def __init__(self,stream):
        self.stream = stream
    def write(self,data):
        self.stream.write(data)
        self.stream.flush()
    def write(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

# Make sure python doesn't try to buffer output and pushes it to STDOUT immediately
sys.stdout = Unbuffered(sys.stdout)

def check_job(job_id):
    done = False
    latest_progress = 0
    while not done:
        check_job = requests.get('https://' + FIREWALL_IP + JOB_CHECK_URL + job_id + JOB_CHECK_URL2 + api_key, verify=False)
        check_job = BeautifulSoup(check_job.text, 'html.parser')
        if check_job.result.result.text == 'PEND':
            if check_job.progress.text != latest_progress:
                latest_progress = check_job.progress.text
                print(check_job.progress.text + '%.', end='')
            else:
                print('.', end='')
        elif check_job.result.result.text == 'FAIL':
            return False
        else:
            return True
        time.sleep(5)

print('Welcome to the Automated Palo Alto Firewall Upgrade Tool')
print('Minimum PAN-OS version required: v7.1')
print('NOTE: superuser account required to download/install PAN-OS image')
print('NOTE: This script depends on the requests and bs4 python modules.\n')

FIREWALL_IP = input('Please enter the IP address of the firewall to be upgraded: ')

admin = input('Please enter admin username with API permissions: ')
password = getpass.getpass('Please enter API administrator password: ')

# Request API key from firewall
print('Retrieving API key')
req_key = requests.get('https://' + FIREWALL_IP + KEYGEN_URL + admin + '&password=' + password, verify=False)
key_soup = BeautifulSoup(req_key.text, 'html.parser')
api_key = key_soup.key.text

# Get current firewall PAN-OS version
pan_ver = requests.get('https://' + FIREWALL_IP + OS_VER_URL + api_key, verify=False)
pan_ver = BeautifulSoup(pan_ver.text, 'html.parser')
pan_ver = pan_ver.find('sw-version').text

print('Downloading list of available PAN-OS software versions. Please wait')
# Check for available software versions through PANW updates portal
r = requests.get('https://' + FIREWALL_IP + CHECK_SW_URL + api_key, verify=False)

# Beautify the JSON response from the firewall
request_soup = BeautifulSoup(r.text, 'html.parser')
for i in request_soup.find_all('version'):
    versions.append(i.text)

# Sort version responses in descending order
versions.sort(reverse=True)

# Retrieve latest content update
print('\nLatest content update is required prior to upgrade.')
print('Downloading latest content update. Please wait')
content_dl = requests.get('https://' + FIREWALL_IP + CONTENT_URL + api_key, verify=False)
content_dl = BeautifulSoup(content_dl.text, 'html.parser')
content_dl_success = check_job(content_dl.job.text)
if content_dl_success:
    print('\nLatest content update downloaded successfully')
elif not content_dl_success:
    print('Failed to download latest content update. Script terminating')
    quit(1)

# Install latest content update
proceed = input('Ready to install latest content update (Y/N)? ')

if proceed.upper() == 'N':
    a = 0
    #print('Script terminating')
    #quit()
elif proceed.upper() == 'Y':
    print('Installing latest content update')
    cu_install = requests.get('https://' + FIREWALL_IP + CU_INSTALL_URL + api_key, verify=False)
    cu_install = BeautifulSoup(cu_install.text, 'html.parser')
    cu_install_success = check_job(cu_install.job.text)
    if cu_install_success:
        print('\nLatest content update installed successfully')
    elif not content_dl_success:
        print('Failed to install latest content update. Script terminating')
        quit(1)
    else:
        print('Invalid selection - Script terminating')
        quit()

while True:
    # Prompt for version of PAN-OS to download
    print('\nCurrent PAN-OS Version: ' + pan_ver)
    print('\nList of available PAN-OS software\n',end='')
    for x in range(0,len(versions)):
        if x % 6 == 0 and x != 0:
            print('%10s' % versions[x] + '\n',end='')
        else:
            print('%10s' % versions[x],end='')

    up_ver = input('\n\nPlease type the PAN-OS version to download (type exactly as shown above): ')

    # Make sure version selected is higher than current release
    if up_ver not in versions:
        print('You made an invalid selection.')
        print('Please make another selection or CTRL-C to quit.')
    elif up_ver <= pan_ver:
        print('You selected a version less than or equal to the current PAN-OS running on the firewall')
        print('Please make another selection or CTRL-C to quit.')
    else:
        break

# Pre-load PAN-OS image
print('Version selected: ' + up_ver)
print('\nAn account with superuser privileges is required to download and install PAN-OS image updates')
admin_user = input('Please enter the superuser username: ')
admin_pass = getpass.getpass('Please enter the superuser password: ')

print('Retrieving superuser API key')
admin_req_key = requests.get('https://' + FIREWALL_IP + KEYGEN_URL + admin_user + '&password=' + admin_pass, verify=False)
admin_key_soup = BeautifulSoup(admin_req_key.text, 'html.parser')
admin_api_key = admin_key_soup.key.text

print('\nDownloading PAN-OS image version ' + up_ver + '. Please wait')

panos_dl = requests.get('https://' + FIREWALL_IP + PANOS_REQ_URL1 + up_ver + PANOS_REQ_URL2 + admin_api_key, verify=False)
panos_dl = BeautifulSoup(panos_dl.text, 'html.parser')
panos_dl_success = check_job(panos_dl.job.text)

if panos_dl_success:
    print('\n\nPAN-OS image version ' + up_ver + ' downloaded successfully')
elif not panos_dl_success:
    print('Failed to download PAN-OS upgrade image. Script terminating')
    quit(1)

# Prompt user to proceed with upgrade
print('\nPlease ensure you have a configuration backup before proceeding')
up_proceed = input('\nAre you ready to install PAN-OS version ' + up_ver + '? ')
if up_proceed.upper() == 'N':
    print('Script terminating')
    quit()
elif up_proceed.upper() != 'Y':
    print('Invalid selection - Script terminating')
    quit()
elif up_proceed.upper() == 'Y':
    print('Installing PAN-OS version: ' + up_ver + '. Please wait')
    panos_up_install = requests.get('https://' + FIREWALL_IP + PANOS_UP_URL1 + up_ver + PANOS_UP_URL2 + admin_api_key, verify=False)
    panos_up_install = BeautifulSoup(panos_up_install.text, 'html.parser')
    panos_up_success = check_job(panos_up_install.job.text)
    if panos_up_success:
        print('\nPAN-OS version ' + up_ver + ' installed successfully')
    elif not panos_up_success:
        print('Failed to install PAN-OS version ' + up_ver + '. Script terminating')
        quit(1)

    reboot = input('Reboot firewall now (Recommended) (Y/N)? ')
    if reboot.upper() == 'Y':
        print('Executing reboot. Please try accessing the WEB UI in approximately 10-15 minutes')
        reboot = requests.get('https://' + FIREWALL_IP + REBOOT_URL + admin_api_key,verify=False)
        print('\nReboot has been initiated')
        quit(0)
    else:
        print('Scripting terminating')
        quit(1)
