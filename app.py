import json
import os
from pprint import pprint
from pymongo import *
from flask import *
from py2neo import *;


app = Flask(__name__)


authenticate("localhost:7474", "neo4j", "alwar301")
graph = Graph();


client = MongoClient()
db= client.vid
videos = db.videos


def init_user(user_id ,ip_address, video_id):
	graph.run("MERGE(u:user{ _id:'" + user_id + "', ip_address:'" + ip_address + "' })")
	cursor = graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id='" + str(video_id) + "' AND u._id= '" + str(user_id) + "' RETURN (u)")
	views = 1
	isWatched = cursor.evaluate()
	if isWatched!=None:
		views = 1 + int(graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id='" + str(video_id) + "' AND u._id= '" + str(user_id) + "' RETURN r.views").evaluate())
		print("views=" + str(views))		
		graph.run("MATCH (v:video)-[r:WATCHED]-(u:user) WHERE v._id = '" + str(video_id) + "' AND u._id = '" + str(user_id) + "' SET r.views = '" + str(views) + "' RETURN r.views");
	else:
		views = graph.run("MATCH (v:video), (u:user) WHERE v._id = '" + str(video_id) + "' AND u._id = '" + str(user_id) + "' CREATE (v)-[r:WATCHED { views:'" + str(views) + "'}]->(u)");
		print("views=" + str(views))

def cursor_to_list(C):
	return [rec for rec in C]

def test_related_videos(video_id):
	return cursor_to_list(graph.run("MATCH (v1:video)-[r:COMMON_TAGS]-(v2:video) WHERE v1._id = '" + str(video_id) + "' return v2._id "));

def recommendations(user_id, video_id):
	result1 = cursor_to_list(graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id = '" + str(video_id) + "' return u._id "))
	#result1 = graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id = '" + str(video_id) + "' return u ").evaluate();
	result2 = cursor_to_list(graph.run("MATCH (u:user)-[r:COMMON_TAGS]-(v:video) WHERE v._id = '" + str(video_id) + "' return u._id "));
	result3 = cursor_to_list(graph.run("MATCH (u11:user)-[r11:WATCHED]-(v11:video) where v11._id =  '"+ str(video_id)  + "' WITH u11 MATCH (v1:video)-[r:COMMON_TAGS]-(v2:video) WHERE v1._id = '" + str(video_id) + "' WITH v2, u11 MATCH (v3:video)-[r:WATCHED]-(u1:user) WHERE v3._id = v2._id AND u11._id = u1._id  RETURN u1, v3"))
	print(result1)

def same_session_vids(video_id):
	return cursor_to_list(graph.run("MATCH (v1:video)-[r:SAME_SESSION]-(v2:video) WHERE v1._id = '" + str(video_id) + "' AND r.weight > 0 RETURN v2._id ORDER BY r.weight"))	

def add_session_edge(video_id_prev,video_id_cur):
	views = 1 + int(graph.run("MATCH (v1:video)-[r:SAME_SESSION]-(v2:video) WHERE v1._id='" + str(video_id_prev) + "' AND v2._id= '" + str(video_id_cur) + "' RETURN r.weight").evaluate())
	graph.run("MATCH (v1:video)-[r:SAME_SESSION]-(v2:video) WHERE v1._id = '" + str(video_id_prev) + "' AND v2._id = '" + str(video_id_cur) + "' SET r.weight = " + str(views) + " RETURN r.weight")

def compare(i1,i2):
	if i1['score'] < i2['score']:
		return 1;
	elif i1['score'] > i2['score']:
		return -1;
	else:
		return 0;

def searchMongo(query):
	res = db.videos.find({"$text": {"$search": query}}, {"score": {"$meta": "textScore"}})
	result = []
	for r in res:
		result.append(r)
	result = sorted(result, cmp = compare)
	return result

def searchMongoById(id):
	return db.videos.find({"videoInfo.id": id})	

@app.route('/', methods = ['POST', 'GET'])
def home():
	if request.method == 'POST':
		query = request.form['query']
		result = searchMongo(query)
		return render_template('index.html', result = result)
	else:
		return render_template('index.html', result = [])

def neo2mongo(neo4j_videos):
	videos = []
	for v in neo4j_videos:
		print v
		for r in searchMongoById(v["v2._id"]):
			videos.append(r)
	return videos

@app.route('/video', methods = ['POST', 'GET'])
def video():
	if request.method == 'GET':
		video_id = request.args.get('_id')
		current_video = searchMongoById(video_id)
		related_videos = neo2mongo(test_related_videos(video_id))
		return render_template('video.html', current_video = current_video, related_videos = related_videos)
	else:
		return render_template('video.html', result = [])



if __name__ == '__main__':
	app.run()