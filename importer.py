from endomondo import Endomondo
import configparser 
import sqlite3
from pymongo import MongoClient
from datetime import datetime

class RowManager:

	def __init__(self, row, cursor):
		self.row = row
		self.col_names = list(map(lambda x: x[0], cursor.description))

	def get(self, column):
		return self.row[self.col_names.index(column)]


conn = sqlite3.connect('../Mundo/db/development.sqlite3', detect_types=sqlite3.PARSE_COLNAMES)
c = conn.cursor() 
client = MongoClient('mongodb://MONGO_URL_HERE')
db = client.mundo_backup
mongo_col = db.workouts

users =[]
for row in c.execute('Select * from users'):
	users.append(RowManager(row, c))

for user in users:
	print(user.get('username'))
	endomondo = Endomondo(user.get('email'), user.get('password'))

	workouts = endomondo.workout_list()

	for w in workouts:
		w.data['m_username'] = user.get('username')
		w.data['m_user_id'] = user.get('id')
		try:
			print(w.data)
			mongo_col.insert(w.data)
		except:
			print('Workout not inserted in mongodb, ID %s already exists' % w.id)

		c.execute("""replace into workouts (endo_workout_id, user_id, username, sport, 
			endo_sport_id, distance_km, start_time, duration_sec, created_at) 
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
			(w.id, user.get('id'), user.get('username'), w.summary, 
				w.sport, w.distance_km, w.start_time, w.duration_sec, 
				datetime.now()))
		print(w.start_time, w.duration_sec, w.id, w.sport, 
			w.note, w.summary, w.speed_kmh_avg, w.distance_km)

	conn.commit()

client.disconnect()
c.close()
conn.close()
