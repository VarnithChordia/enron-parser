import re
from os import path, listdir
import sys
import json

#
# Precompiled patterns for performance
#
time_pattern = re.compile("Date: (?P<data>[A-Z][a-z]+\, \d{1,2} [A-Z][a-z]+ \d{4} \d{2}\:\d{2}\:\d{2} \-\d{4} \([A-Z]{3}\))")
subject_pattern = re.compile("Subject: (?P<data>.*)")
sender_pattern = re.compile("From: (?P<data>.*)")
recipient_pattern = re.compile("To: (?P<data>.*)")
cc_pattern = re.compile("cc: (?P<data>.*)")
bcc_pattern = re.compile("bcc: (?P<data>.*)")
msg_start_pattern = re.compile("\n\n", re.MULTILINE)
msg_end_pattern = re.compile("\n+.*\n\d+/\d+/\d+ \d+:\d+ [AP]M", re.MULTILINE)

#
# Function: parse_email
# Arguments: pathname - relative path of folder/file to be parsed
#            orig     - whether this call is the original, used for writing to file
# Returns: none
# Effects: dumps json into file
#
feeds = []
users = {}
threads = {}
def parse_email(pathname, orig=True):
    if path.isdir(pathname):
        print(pathname)
        emails = []
        for child in listdir(pathname):
            # only parse visible files
            if child[0] != ".":
                parse_email(path.join(pathname, child), False)
    else:
        print("file %s" % pathname)
        with open(pathname) as TextFile:
            text = TextFile.read()
            try:
                time = time_pattern.search(text).group("data").replace("\r", "").replace("\n", "")
                subject = subject_pattern.search(text).group("data").replace("\r", "").replace("\n", "")

                sender = sender_pattern.search(text).group("data").replace("\r", "").replace("\n", "")

                recipient = recipient_pattern.search(text).group("data").split(", ")
                cc = cc_pattern.search(text).group("data").split(", ")
                bcc = bcc_pattern.search(text).group("data").split(", ")
                msg_start_iter = msg_start_pattern.search(text).end()
                try:
                    msg_end_iter = msg_end_pattern.search(text).start()
                    message = text[msg_start_iter:msg_end_iter]
                except AttributeError: # not a reply
                    message = text[msg_start_iter:]
                message = re.sub("[\n\r]", " ", message)
                message = re.sub("  +", " ", message)
            except AttributeError:
                logging.error("Failed to parse %s" % pathname) 
                return None
            # get user and thread ids
            sender_id = get_or_allocate_uid(sender)
            recipient_id = [get_or_allocate_uid(u.replace("\r", "").replace("\n", "")) for u in recipient if u!=""]
            cc_ids = [get_or_allocate_uid(u.replace("\r", "").replace("\n", "")) for u in cc if u!=""]
            bcc_ids = [get_or_allocate_uid(u.replace("\r", "").replace("\n", "")) for u in bcc if u!=""]
            thread_id = get_or_allocate_tid(subject)
        entry =  {"time": time, "thread": thread_id, "sender": sender_id, "recipient": recipient_id, "cc": cc_ids, "bcc": bcc_ids, "message": message}
        feeds.append(entry)
    if orig:
        try:
            with open('messages.json', 'w') as f:
                json.dump(feeds, f)
            with open('users.json', 'w') as f:
                json.dump(users, f)
            with open('threads.json', 'w') as f:
                json.dump(threads, f)
        except IOError:
            print("Unable to write to output files, aborting")
            exit(1)

#
# Function: get_or_allocated_uid
# Arguments: name - string of a user email
# Returns: unique integer id
#
def get_or_allocate_uid(name):
     if name not in users:
         users[name] = len(users)
     return users[name]

#
# Function: get_or_allocate_tid
# Arguments: name - string of email subject line
# Returns: unique integer id
#
def get_or_allocate_tid(name):
    parsed_name = re.sub("Re: ", "", name)
    if parsed_name not in threads:
        threads[parsed_name] = len(threads)
    return threads[parsed_name]

parse_email(sys.argv[1])
