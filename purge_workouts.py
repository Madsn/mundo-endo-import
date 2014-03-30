from pymongo import MongoClient

def purge_collection(collection):
	items = collection.find()
	for i in items:
		collection.remove({"_id": i.get('_id')})
	
client = MongoClient('mongodb://MONGO_URL_HERE')
db = client.mundo_backup

workout_col = db.workouts
purge_collection(workout_col)

#user_col = db.users
#purge_collection(user_col)
