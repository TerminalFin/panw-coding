from packaging import version
import urllib3
import xml.etree.ElementTree as ET
import getpass
import time
import sys

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
    def write(self,datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

# Make sure python doesn't try to buffer output and pushes it to STDOUT immediately
sys.stdout = Unbuffered(sys.stdout)

def pause():
    input("Press any key to continue...")

def check_job(job_id):
    done = False
    latest_progress = 0
    while not done:
        # Get current firewall PAN-OS version
        response = request.request('GET', JOB_CHECK_URL + job_id + JOB_CHECK_URL2 + api_key)

        # Parse XML response and extract job status
        output = ET.fromstring(response.data)
        status = output.find('result/job/result').text
        progress = output.find('result/job/progress').text

        if status == 'PEND':
            if progress != latest_progress:
                latest_progress = progress
                print(progress + '%.', end='')
            else:
                print('.', end='')
        elif status == 'FAIL':
            return False
        else:
            return True
        time.sleep(5)

print('Welcome to the Automated Palo Alto Firewall Upgrade Tool')
print('Minimum PAN-OS version required: v7.1\n')
print('NOTE: superuser account required to download/install PAN-OS image')
print('NOTE: This script depends on the packaging module (pip install packaging)')

FIREWALL_IP = input('Please enter the IP address of the firewall to be upgraded: ')

# Define the request variable to be used for REST API calls
# cert_reqs='CERT_NONE' and assert_hostname=False ignores errors caused by self-signed certificates
request = urllib3.HTTPSConnectionPool(FIREWALL_IP, cert_reqs='CERT_NONE',assert_hostname=False)

admin = input('Please enter admin username with API permissions: ')
password = getpass.getpass('Please enter API administrator password: ')

# Request API key from firewall
print('Retrieving API key')
response = request.request('GET', KEYGEN_URL + admin + '&password=' + password)

# Parse XML response and extract API key
output = ET.fromstring(response.data)
api_key = output.find('result/key').text

# Get current firewall PAN-OS version
response = request.request('GET', OS_VER_URL + api_key)

# Parse XML response and extract current PAN-OS version
output = ET.fromstring(response.data)
pan_ver = output.find('result/system/sw-version').text

print('Downloading list of available PAN-OS software versions. Please wait')
# Check for available software versions through PANW updates portal

response = request.request('GET', CHECK_SW_URL + api_key)

# Parse XML response and extract available software versions
output = ET.fromstring(response.data)

for item in output.findall('result/sw-updates/versions/entry/version'):
     versions.append(item.text)

# Sort version responses in descending order
versions.sort(reverse=True)

# Retrieve latest content update
print('\nLatest content update is required prior to upgrade.')
print('Downloading latest content update. Please wait')

# Get current firewall PAN-OS version
response = request.request('GET', CONTENT_URL + api_key)

# Parse XML response and extract content download job ID
output = ET.fromstring(response.data)
content_job_id = output.find('result/job').text

content_dl_success = check_job(content_job_id)
if content_dl_success:
    print('\nLatest content update downloaded successfully')
elif not content_dl_success:
    print('Failed to download latest content update. Script terminating')
    quit(1)

# Install latest content update
proceed = input('Ready to install latest content update (Y/N)? ')

if proceed.upper() == 'N':
    print('Script terminating')
    quit()
elif proceed.upper() == 'Y':
    print('Installing latest content update')
    # Get current firewall PAN-OS version
    response = request.request('GET', CU_INSTALL_URL + api_key)

    # Parse XML response and extract content installation job ID
    output = ET.fromstring(response.data)
    cu_install_job_id = output.find('result/job').text

cu_install_success = check_job(cu_install_job_id)
if cu_install_success:
    print('\nLatest content update installed successfully')
elif not content_dl_success:
    print('Failed to install latest content update. Script terminating')
    quit(1)
else:
    print('Invalid selection - Script terminating')
    quit(1)

while True:
    # Prompt for version of PAN-OS to download
    print('\nList of available PAN-OS software\n',end='')
    for x in range(0,len(versions)):
        if x % 5 == 0 and x != 0:
            print('\n%14s' % versions[x],end='')
        else:
            print('%14s' % versions[x],end='')

    up_ver = input('\n\nCurrent PAN-OS Version: ' + pan_ver + '\nPlease type the PAN-OS version to download (type exactly as shown above): ')

    # Make sure version selected is higher than current release
    if up_ver not in versions:
        print('You made an invalid selection.')
        print('Please make another selection or CTRL-C to quit.')
        pause()
    elif version.parse(up_ver) < version.parse(pan_ver):
        print('You selected a version older than the current PAN-OS running on the firewall')
        print('Downgrading is currently not supported by this script')
        print('Please make another selection or CTRL-C to quit.')
        pause()
    elif version.parse(up_ver) == version.parse(pan_ver):
        print('You selected the same PAN-OS version the firewall is currently running')
        pause()
    else:
        break

# Pre-load PAN-OS image
print('Version selected: ' + up_ver)
print('\nAn account with superuser privileges is required to download and install PAN-OS image updates')
admin_user = input('Please enter the superuser username: ')
admin_pass = getpass.getpass('Please enter the superuser password: ')

print('Retrieving superuser API key')

# Get superuser API key
response = request.request('GET', KEYGEN_URL + admin_user + '&password=' + admin_pass)

# Parse XML response and extract superuser API key
output = ET.fromstring(response.data)
admin_api_key = output.find('result/key').text

print('\nDownloading PAN-OS image version ' + up_ver + '. Please wait')

# Get current PAN-OS download Job ID
response = request.request('GET', PANOS_REQ_URL1 + up_ver + PANOS_REQ_URL2 + admin_api_key)

# Parse XML response and extract API key
output = ET.fromstring(response.data)
panos_dl_job_id = output.find('result/job').text

panos_dl_success = check_job(panos_dl_job_id)

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
    
    # Install the selected PAN-OS version
    response = request.request('GET', PANOS_UP_URL1 + up_ver + PANOS_UP_URL2 + admin_api_key)

    # Parse XML response and extract installation job ID
    output = ET.fromstring(response.data)
    panos_upg_job_id = output.find('result/job').text

    panos_up_success = check_job(panos_upg_job_id)

    if panos_up_success:
        print('\nPAN-OS version ' + up_ver + ' installed successfully')
    elif not panos_up_success:
        print('Failed to install PAN-OS version ' + up_ver + '. Script terminating')
        quit(1)

    reboot = input('Reboot firewall now (Recommended) (Y/N)? ')
    if reboot.upper() == 'Y':
        print('Executing reboot. Please try accessing the WEB UI in approximately 10-15 minutes')
        reboot = request.request('GET', REBOOT_URL + admin_api_key)
        print('\nReboot has been initiated')
        quit(0)
    else:
        print('Scripting terminating')
        quit(1)
