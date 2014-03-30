#!/usr/local/bin/python3.3
# mongodb with collections:
# users - unique index on email, to prevent duplicates
# workouts - unique index on "id". This is the workout id received from endomondo
# 		     by making this unique, we avoid importing duplicates from endomondo
from endomondo import Endomondo
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://MONGO_URL_HERE')
db = client.mundo_backup

user_col = db.users
workout_col = db.workouts
try:
	user_col.insert({"username": "Name1", "email": "xxxx", "password": "xxxx", "last_checked": None})
	user_col.insert({"username": "Name2", "email": "xxxx", "password": "xxxx", "last_checked": None})
except:
	pass

# Alternate between users. Only one user pr execution
user = user_col.find().sort('last_checked', 1).limit(1)[0]
user['last_checked'] = datetime.now()
user_col.update({'_id':user.get('_id')}, user, upsert=False, multi=False)

endomondo = Endomondo(user.get('email'), user.get('password'))

workouts = endomondo.workout_list()

for w in workouts:
	w.data['username'] = user.get('username')
	w.data['user_id'] = user.get('_id')
	try:
		print(w.data)
		workout_col.insert(w.data)
	except:
		print('Workout not inserted in mongodb, ID %s already exists' % w.data['id'])

client.disconnect()
