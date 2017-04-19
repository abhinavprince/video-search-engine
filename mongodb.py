import os
import pymongo
import json
from pymongo import MongoClient

files = os.listdir(os.getcwd() + "/test/")

client = MongoClient()
db = client['vid']
collection = db['videos']
c = 0


for f in files:
	print(f)
	data_file = open(os.getcwd() + "/test/" + f)
	data = json.load(data_file)
	insert_id = collection.insert_one(data).inserted_id
	print(insert_id)
	data_file.close()
	c = c+1
	print(c)


# db.videos.createIndex( {"$**": "text"}, {"weights": { "videoInfo.snippet.title": 10, "videoInfo.snippet.description":7, "videoInfo.snippet.tags":3 }} )