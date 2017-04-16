import os;
import json;
from py2neo import *;

authenticate("localhost:7474", "neo4j", "prince")
graph = Graph();


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


def cursor_to_List(C):
	return [rec for rec in C]
	

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
	

init_user("userid007", "10.9.12.5", "9OKCY28j92A")
init_user("userid0069", "10.9.12.5", "14t3NcNWsYs")


recommendations("userid00", "1a3-a_zaJRM")
