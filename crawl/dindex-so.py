#!/usr/bin/python

import sys
import json
import calendar
from datetime import datetime
import os

def main(filename):
    DATE_2000 = 946684800
    percent = 7.5
    f = open(filename, 'r')
    json_data = json.load(f)
    answerer = json_data['answerer']
    # print json.dumps(answerer, indent=4)
    ar0 = answerer["reputation"]
    norm = 0
    num = 0
    questions = json_data['questions']
    questions = sorted(questions, key=lambda question: question['datetime'])
    for question in questions:
        if not question['datetime']:
            continue
        dt = datetime.strptime(question["datetime"], '%Y-%m-%dT%H:%M:%S')
        t = (calendar.timegm(dt.utctimetuple()) - DATE_2000) / 3600 / 24
        qr = question["questioner_reputation"]
        qs = question["question_votes"]
        as0 = question["answer_votes"]
        interest = pow(1+percent/100, t)
        interest = t
        norm += interest
        num += (qr + qs + as0)/(num/norm + 1.0)*interest
        
        #print t, qr, qs, ar0, as0, num, norm
        #print json.dumps(question, indent=4)
        
    print "{} {} {}".format(filename, ar0, num/norm)
if __name__ == '__main__':
#    main(sys.argv[1])
    for subdirs, dirs, files in os.walk('stackoverflow/'):
        for filename in files:
           main('stackoverflow/' + filename) 
