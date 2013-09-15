# coding: utf-8

from app import db
import requests
import json
data = {'accessToken':'abc', 'fbId':'1234', 'fullname':'ssk', 'imageLink':'foo'}
data['fbId'] = '807033804'
data['fullName'] = 'fateh'
requests.post('http://0.0.0.0:5000/login', data=json.dumps(data), headers = {'content-type': 'application/json'})
requests.post('http://198.199.67.210/login', data=json.dumps(data), headers = {'content-type': 'application/json'})
_
s = requests.session()
s.post('http://198.199.67.210/login', data=json.dumps(data), headers = {'content-type': 'application/json'})
s.post('http://198.199.67.210/user/1/queue', data=json.dumps(data1), headers = {'content-type': 'application/json'})
data2 = {'fromUser':{'userId':1,'accessToken':''}, 'type':'song', 'listened':'false', 'song':{'artist':{'name':'Eels', 'images':{'small':'', 'medium':'','large':'' }}, 'album':{'name': 'Wonderful, Glorious'}, 'name':'New Alphabet', 'images':{'small':'', 'medium':'', 'large':''}}}
s.post('http://198.199.67.210/user/1/queue', data=json.dumps(data2), headers = {'content-type': 'application/json'})
