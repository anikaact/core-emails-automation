import sys

#Folders where the config_files and log_file will be stored
DEV_INFO = sys.path[0] + '/.venv' + '/devices.json'

recip_list = ['anika.thapar@arrcus.com']
#if cc_list is empty, no one will be cc'd
cc_list = []


#if type = 'individual', each device will have an individual message
#if type = 'combined', all device information will be compiled into one message

#type = 'individual'
type = 'combined'
#type = 'combeine'