#!/usr/bin/python
"""
	Program Developed for the course: MultiDisciplinary Project

	The program get as a argument a String that corresponds to the username that 
	we want to looking for into GitHub. As a result we have a list formed
	by a tuple {name, url} which matched with the given String.

	@author: Ferran B.
"""
import urllib
import urllib2
import time
from time import mktime
import datetime as dtpackage
from datetime import datetime
import re
import json
from sets import Set
from bs4 import BeautifulSoup
import sys
import os
from concurrent import futures
from futures import ThreadPoolExecutor
import contextlib
import codecs
import httplib2
import csv
import time

# Auxiliar functions

THREADS = 10

GITHUB_URL = 'https://github.com'

def read_page(page):
    text = ''
    while True:
        try:
            with contextlib.closing(urllib2.urlopen(page)) as response:
                text = response.read()
            break
        except Exception as e:
            print "ERROR: ", e, page
            time.sleep(5)
    return text

def process_user(username, fullname):
    filename = 'github/{}.csv'.format(username)
    filename_tmp = '{}.tmp'.format(filename)
    with open(filename_tmp, 'a'):
        os.utime(filename_tmp, None)
    uri_param = httplib2.iri2uri(fullname.replace(' ', '+'))
    url = u'{}/search?q={}&type=Users'.format(GITHUB_URL, uri_param)
    text = read_page(url)
    soup = BeautifulSoup(text)
    user_info = soup.find(class_='user-list-info')
    if not user_info:
        os.rename(filename_tmp, filename)
        soup.decompose()
        return
    a = user_info.find('a')
    github_username = a['href'][1:]
    with open(filename_tmp, 'w') as f:
        f.write(github_username + '\n')
        f.close()
    print "link stackoverflow '{}' to github '{}'".format(username, github_username)
    soup.decompose()
    commits = process_days(github_username, filename_tmp)
    os.rename(filename_tmp, filename)
    if github_username in CACHE:
        del CACHE[github_username]

def process_days(username, filename):
    url = u'{}/users/{}/contributions_calendar_data'.format(GITHUB_URL, username)
    days = read_page(url)
    days = json.loads(days)
    for day in days:
        if day[1] != 0:
            dt = day[0].replace('/', '-')
            parse_day(username, dt, filename)

def parse_day(username, day, filename):
    print u"{}: day={}".format(username, day)
    url = u'{}/{}?tab=contributions&from={}'.format(GITHUB_URL, username, day)
    text = read_page(url)
    soup = BeautifulSoup(text)
    header = soup.find(class_='conversation-list-heading')
    urls = []
    if header.get_text().find('commits') != -1:
        ul = soup.find(class_='simple-conversation-list')
        for a in ul.find_all('a'):
            urls.append(a['href'])
    soup.decompose()
    for url in urls:
        parse_repository(username, url, filename)

CACHE = {}

def parse_repository(username, url, filename):
    user_cache = CACHE.get(username)
    if not user_cache:
        user_cache = Set()
        CACHE[username] = user_cache
    if url in user_cache:
        return []
    user_cache.add(url)
    url = GITHUB_URL + url
    text = read_page(url)
    soup = BeautifulSoup(text)
    commits = soup.find_all(class_='gobutton')
    urls = []
    for a in commits:
        urls.append(a['href'])
    soup.decompose()
    results = []
    for url in urls:
        data = parse_commit(username, url)
        results.append(data)
    with contextlib.closing(open(filename, 'ab')) as csvfile:
        writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
        for commit in results:
            writer.writerow(commit)
        csvfile.close()

def parse_commit(username, url):
    print u"{}: {}".format(username, url)
    url = GITHUB_URL + url
    text = read_page(url)
    soup = BeautifulSoup(text)
    toc = soup.find(id='toc')
    strong = toc.find('strong').find_next('strong')
    loc = strong.get_text().split(' ')[0]
    loc = loc.replace(',', '')
    loc = int(loc)
    utc = soup.find('time')['datetime']
    utc = utc[:-6] # ignore timezone
    soup.decompose()
    return [url, utc, loc]

#def process_user(username, fullname): 
#    print u'creating thread for user; username={}; full name={}'.format(username, fullname)
#    result = get_user(username, fullname)
#    f = open('github/{}.json'.format(username), 'w')
#    f.write(json.dumps(result, indent=4))
#    f.close()

if __name__ == '__main__':
    from guppy import hpy
    h = hpy()
    executor = ThreadPoolExecutor(max_workers=THREADS)
    thread = None
    for subdirs, dirs, files in os.walk('stackoverflow/'):
        i = 0
        for filename in files:
            username = filename[:-5]
            github_filename = 'github/{}.csv'.format(username)
            if os.path.isfile('{}.tmp'.format(github_filename)):
                os.remove('{}.tmp'.format(github_filename)) 
            if os.path.isfile(github_filename):
                print u"skip {}".format(username)
                continue
            f = codecs.open('stackoverflow/{}'.format(filename), 'r', 'utf-8')
            data = json.load(f)
            f.close()
            fullname = data['answerer']['name']
#            if i % (THREADS * 2) == 0:
#                if thread:
#                    thread.result()
#                thread = executor.submit(process_user, username, fullname)
#            else:  
#                executor.submit(process_user, username, fullname)
            print u"put in thread pool user '{}'".format(username)
            
            process_user(username, fullname)
            i += 1
            print h.heap()
            sys.exit(0)
    executor.shutdown(wait=True)
