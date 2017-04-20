import json
import os
from pprint import pprint
from pymongo import *
from flask import *
from py2neo import *
import pymysql.cursors
# import functools

app = Flask(__name__)
app.secret_key = 'any random string'

authenticate("localhost:7474", "neo4j", "alwar301")
graph = Graph();


client = MongoClient()
db= client.vid
videos = db.videos

connection = pymysql.connect(host='localhost',user='root',password='1234',db='VIDEOS',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor);

"""
 - called whenever user watched a video
 - increaments the weight of the edge between user and video by one
 - stores latest viewed time as an attribute of edge
"""
def init_user(user_id ,ip_address, video_id):
	# print user_id , ip_address , video_id
	graph.run("MERGE(u:user{ _id:'" + user_id + "', ip_address:'" + ip_address + "' })")
	cursor = graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id='" + str(video_id) + "' AND u._id= '" + str(user_id) + "' RETURN (u)")
	views = 1
	isWatched = cursor.evaluate()
	if isWatched!=None:
		views = 1 + int(graph.run("MATCH (u:user)-[r:WATCHED]-(v:video) WHERE v._id='" + str(video_id) + "' AND u._id= '" + str(user_id) + "' RETURN r.views").evaluate())
		print("views=" + str(views))		
		graph.run("MATCH (v:video)-[r:WATCHED]-(u:user) WHERE v._id = '" + str(video_id) + "' AND u._id = '" + str(user_id) + "' SET r.views = '" + str(views) + "', r.time = timestamp() RETURN r.views");
	else:
		views = graph.run("MATCH (v:video), (u:user) WHERE v._id = '" + str(video_id) + "' AND u._id = '" + str(user_id) + "' CREATE (v)-[r:WATCHED { views:'" + str(views) + "',time : timestamp()}]->(u)");
		print("views=" + str(views))

def cursor_to_list(C):
	return [rec for rec in C]

def test_related_videos(video_id):
	return cursor_to_list(graph.run("MATCH (v1:video)-[r:COMMON_TAGS]-(v2:video) WHERE v1._id = '" + str(video_id) + "' return v2._id"))
	
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
	# result = sorted(result, key=functools.cmp_to_key(compare))
	return result

def searchMongoById(id):
	return db.videos.find({"videoInfo.id": id})	

@app.route('/', methods = ['POST', 'GET'])
def home():
	if "username" not in session:
		return redirect("/login")		
	if request.method == 'POST':
		query = request.form['query']
		result = searchMongo(query)
		return render_template('index.html', result = [session['username'],result])
	else:
		historyv = history()
		return render_template('index.html', result = [session['username'],historyv])

def neo2mongo(neo4j_videos):
	videos = []
	for v in neo4j_videos:
		# print v
		for r in searchMongoById(v["v2._id"]):
			videos.append(r)
	return videos

def verify_user(username,password):
	c = connection.cursor()
	sql = "SELECT `username`, `password` FROM `users` WHERE `username`=%s"
	c.execute(sql, (username,))
	L = list(c);
	if len(L) > 0:
		if L[0]['password'] == password:
			session['username'] = username
			return 1
		else:
			return 0
	else:
		return 2

@app.route('/register', methods = ['POST', 'GET'])
def register():
	# print "in register"
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		valid = create_user(username,password)
		return render_template('login.html', result = valid)

@app.route('/signOut', methods = ['POST', 'GET'])
def signout():
	session.pop('username',None)
	return redirect("/login")

def create_user(username,password):
	c = connection.cursor()
	valid = verify_user(username,password)
	if valid == 2:
		sql = "INSERT INTO `users` (`username`, `password`) VALUES (%s,%s)"
		c.execute(sql, (username,password))
		connection.commit()
		return 10
	else:
		return 5

@app.route('/video', methods = ['POST', 'GET'])
def video():
	if request.method == 'GET':
		video_id = request.args.get('_id')
		current_video = searchMongoById(video_id)
		init_user(session['username'],request.remote_addr,video_id)
		related_video = neo2mongo(test_related_videos(video_id))
		return render_template('video.html', current_video = current_video, related_videos = related_video)
	else:
		return render_template('video.html', result = [])


@app.route('/login', methods = ['POST', 'GET'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		valid = verify_user(username,password)
		if valid != 1:
			return render_template('login.html', result = valid)
		else:
			return render_template('index.html', result = [session['username'],[]])
	else:
		return render_template('login.html', result = [])


def history():
	return neo2mongo( graph.run("MATCH (u:user)-[r:WATCHED]-(v2:video) WHERE u._id = '"+session['username']+"' RETURN v2._id ORDER BY r.time DESC"))



def subscribe(user_id, channel_id):
	graph.run("MATCH (u:user), (c:channel) where u._id = '" + str(user_id) + "' AND c._id = '" + str(channel_id) + "' CREATE (u)-[r1:SUBSCRIBED]-(r)")

def unsubscribe(user_id, channel_id):
	graph.run("MATCH (u:user)-[r:SUBSCRIBED]-(c:channel) where u._id = '" + str(user_id) + "' AND c._id = '" + str(channel_id) + "' DELETE r")

def like(user_id, video_id):
	graph.run("MATCH (u:user), (v:video) where u._id = '" + str(user_id) + "' AND v._id = '" + str(video_id) + "' CREATE (u)-[r1:LIKED]-(r)")

def unlike(user_id, video_id):
	graph.run("MATCH (u:user)-[r:LIKED]-(v:video) where u._id = '" + str(user_id) + "' AND v._id = '" + str(video_id) + "' DELETE r")

def dislike(user_id, video_id):
	graph.run("MATCH (u:user), (v:video) where u._id = '" + str(user_id) + "' AND v._id = '" + str(video_id) + "' CREATE (u)-[r1:DISLIKED]-(r)")

# CHANGE NAME OF THIS FUNCTION...LOL
def undislike(user_id, video_id): 
	graph.run("MATCH (u:user)-[r:DISLIKED]-(v:video) where u._id = '" + str(user_id) + "' AND v._id = '" + str(video_id) + "' DELETE r")

# creates a node playlist{name, user}
def create_playlist(user_id, playlist_name):
	graph.run("CREATE (p:playlist{ name: '" + str(playlist_name) + "', user: '" + str(user_id) + "' })")

# creates a relationship "ADDED" between video and user's playlist
def add_to_playlist(user_id, playlist_name, video_id):
	graph.run("MATCH (u:user), (p:playlist), (v:video) where u._id = '" + str(user_id) + "', AND p.name = '" + str(playlist_name) + "', AND p.user = '" + user_id  + "' CREATE (v)-[r:ADDED]-(p)")




if __name__ == '__main__':
	app.run()