# Script Name:                   core_emails.py
# Description:                   core_emails.py sends emails with core information every t hours
# Author:                        Anika Thapar
# Date:                          13 June 2024
# Inputs for this script:        DEV_INFO(.json file), recip_list([]), cc_list([]), type(string)
#
# Output the script generates:   1. Generates core files for each device
#                                2. Generates emails with core file information
#                                3. Sends emails to recipients
#
# Flow of the script:            1. SSh into devices and get core information
#                                2. Stores core information in respective files
#                                3. Checks if we should send individual messages for each core or combined message
#                                4. Access files to store information in the body of message(s)
#                                4. Sends message(s) to list of recipients/ccs
# Usage:
#      - Execute the following in your Linux cli: python3 core_emails.py

import pexpect
import threading
import json
from appscript import app, k
import time
from constants import DEV_INFO, recip_list, cc_list, type

#   parameters:     lines, and filename
#   functionality:  1. creates a file using filename.
#                   2. Stores lines in filename.txt
def file_lines(lines, filename):
  with open(filename, 'w') as file:
     file.write('\n'.join(lines[2:len(lines) - 1]))


#   parameters:     username, ip, pwd
#   functionality:  1. ssh into the device
#                   2. show cores
#                   3. store cores in ls_output
#                   4. store ls_output in respective ipcore.txt file
#   helpers:        file_cores
def store_cores(username, ip, pwd):
  child = pexpect.spawn(f"ssh {username}@{ip}")
  child.expect('password:')
  child.sendline(f"{pwd}")
  child.expect('#')
  child.sendline('cli')
  child.expect('#')
  child.sendline("show core")
  child.expect('#')
  ls_output = child.before.decode('utf-8').splitlines()
  file_lines(ls_output, f"{ip}core.txt")
  child.sendline('exit')
  child.close()

#   parameters:     json_file
#   functionality:  1. open json_file (devices.json)
#                   2. store password, username, and ip addresses using json_file
#                   3. use username, password, ip address to store core information in respective ipcore.txt files
#   helpers:        get_core
def multi_threading(json_file):
  with open(json_file, 'r') as f:
      data = json.load(f)
  password = data['credentials']['password']
  username = data['credentials']['user']
  addresses = [device['ip_address'] for device in data['devices']] #list of ip addresses
  threads = []
  for ip in addresses:
      t = threading.Thread(target=store_cores, args=(username, ip, password))
      t.start()
      threads.append(t)
  for t in threads:
      t.join()

#   parameters:     json_file
#   functionality:  1. creates a list of ip addresses
def ip_lst(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    ip_addresses = [device['ip_address'] for device in data['devices']]  # list of ip addresses
    return ip_addresses

#initializes the outlook client
class Outlook(object):
    def __init__(self):
        self.client = app('Microsoft Outlook')

#represends an email message, including methods to show the message and add recipients.
class Message(object):
    def __init__(self, parent=None, subject='', body='', to_recip=[], cc_recip=[], show_=True):

        #if no parent outlook object is provided, create a new one
        if parent is None: parent = Outlook()
        client = parent.client

        #create a new outgoing message with the specified subject and body
        self.msg = client.make(
            new=k.outgoing_message,
            with_properties={k.subject: subject, k.content: body})

        #add recipients to the message
        self.add_recipients(emails=to_recip, type_='to')
        self.add_recipients(emails=cc_recip, type_='cc')

        #show the message if show_ is true
        if show_: self.show()


    def show(self):
        #open and activate the message
        self.msg.open()
        self.msg.activate()
        self.msg.send() #send the message

    #   parameters:     emails, type
    #   functionality:  1. ensure emails is a list
    #                   2. add each email as a recipient
    def add_recipients(self, emails, type_='to'):
        if not isinstance(emails, list): emails = [emails]
        for email in emails:
            self.add_recipient(email=email, type_=type_)

    #   parameters:     email, type
    #   functionality:  1. determine recipient type (to or cc)
    #                   2. adds the recipient to the message
    def add_recipient(self, email, type_='to'):
        msg = self.msg
        if type_ == 'to':
            recipient = k.to_recipient
        elif type_ == 'cc':
            recipient = k.cc_recipient
        msg.make(new=recipient, with_properties={k.email_address: {k.address: email}})

#   parameters:     json_file, subject, recip_list
#   functionality:  1. executes multi_threading to create files with core information
#                   2. goes through each file and stores file information in the body
#                   3. creates a message object with subject, recipients, and body, which automatically sends the message
#   helpers:        multi_threading, ip_list
def send_message_allinformation(json_file, recip_list, cc_list):
    multi_threading(json_file)
    ip_list = ip_lst(json_file)
    subject = "devices core information"
    body = ''
    for ip in ip_list:
        temp = ''
        temp += ip + " CORE INFORMATION:" + "\n"
        txt_file = f"{ip}core.txt"
        with open(txt_file, 'r') as file:
            cores = file.read()
            temp += cores
            body += temp + "\n" +"\n"
    if len(cc_list) == 0:
        msg = Message(subject=subject, body=body, to_recip=recip_list)
    else:
        msg = Message(subject=subject, body=body, to_recip=recip_list, cc_recip=cc_list)

#   parameters:     ip_address, recip_list
#   functionality:  1. creates subject of the message using ip_address
#                   2. opens ip_addresscore.txt file as the body of the message
#                   3. creates a message object with subject and body, which immediately sends email to recipients
def create_individual_message(ip_address, recip_list, cc_list):
    subject = f"{ip_address} core information"
    body = ''
    with open(f"{ip_address}core.txt", 'r') as file:
        body += file.read()
    if len(cc_list) == 0:
        msg = Message(subject=subject, body=body, to_recip=recip_list)
    else:
        msg = Message(subject=subject, body=body, to_recip=recip_list, cc_recip=cc_list)

#   parameters:     json_file, subject, recip_list
#   functionality:  1. creates a list of ip addresses
#                   2. sends a message for every given ip address
#   helpers:        ip_lst
#                   send_individual_message
def send_individual_messages(json_file, recip_list, cc_list):
    ip_addresses = ip_lst(json_file)  # list of ip addresses
    threads = []
    for ip in ip_addresses:
        t = threading.Thread(target=create_individual_message, args=(ip, recip_list, cc_list))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

#   parameters:     json_file, subject, recip_list
#   functionality:  1. if type is individual, send individual messages for each device
#                   2. if type is combined, send combined message for each device
#                   3.else, print error statement and terminate code
#   helpers:        send_individual message
#                   send_message_allinformation
def send_message(json_file, recip_list, cc_list):
    if type == 'individual':
        send_individual_messages(json_file, recip_list, cc_list)
    if type == 'combined':
        send_message_allinformation(json_file, recip_list, cc_list)
    else:
        print('invalid type: ' + type)
        exit()


def main():
    send_message(DEV_INFO, recip_list, cc_list)





if __name__ == "__main__":
    hours = 2
    while True:
        main()
        print(f"emails sent, next batch will be sent in {2} hours")
        time.sleep(hours * 60 * 60)


