import requests
import getpass
import time
from bs4 import BeautifulSoup

# Ignore warnings due to the use of verify=False in requests.get calls
import warnings
warnings.filterwarnings("ignore")

KEYGEN_URL      = '/api/?type=keygen&user='
TSF_GEN_URL     = '/api/?type=export&category=tech-support'
TSF_RETR_URL    = '/api/?type=export&category=tech-support&action=get&job-id='
JOB_CHECK_URL   = '/api/?type=op&cmd=<show><jobs><id>'
JOB_CHECK_URL2  = '</id></jobs></show>&key='

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


print('Welcome to the Automated Palo Alto Firewall Tech Support File Retrieval Tool')
print('Minimum PAN-OS version required: v7.1')
print('NOTE: superuser account required to generate tech-support file')
print('NOTE: This script depends on the requests and bs4 python modules.\n')

FIREWALL_IP = input('Please enter the IP address of the firewall: ')

admin = input('Please enter admin username with API permissions: ')
password = getpass.getpass('Please enter API administrator password: ')

print('\nAn account with necessary privileges is required to generate/retrieve the TSF')
admin_user = input('Please enter the TSF admin username: ')
admin_pass = getpass.getpass('Please enter the TSF admin password: ')


# Request API key from firewall
print('Retrieving XML API key')
req_key = requests.get('https://' + FIREWALL_IP + KEYGEN_URL + admin + '&password=' + password, verify=False)
key_soup = BeautifulSoup(req_key.text, 'html.parser')
api_key = key_soup.key.text

print('Retrieving TSF admin API key')
admin_req_key = requests.get('https://' + FIREWALL_IP + KEYGEN_URL + admin_user + '&password=' + admin_pass, verify=False)
admin_key_soup = BeautifulSoup(admin_req_key.text, 'html.parser')
admin_api_key = admin_key_soup.key.text

print('Generating tech support file')
gen_tsf = requests.get('https://' + FIREWALL_IP + TSF_GEN_URL, verify=False)
gen_tsf = BeautifulSoup(gen_tsf.text, 'html.parser')
gen_tsf_success = check_job(gen_tsf.job.text)
tsf_job_id = gen_tsf.job.text

if gen_tsf_success:
    print('\n\nTech-support file generated successfully')
elif not gen_tsf_success:
    print('Failed to generate tech-support file. Script terminating')
    quit(1)

print('Retrieving tech support file to working folder')
tsf = requests.get('https://' + FIREWALL_IP + TSF_RETR_URL + tsf_job_id, allow_redirects=True)
open('tsf_' + FIREWALL_IP + '.tgz', 'wb').write(tsf.content)

print('File successfully written to tsf_' + FIREWALL_IP + '.tgz')
