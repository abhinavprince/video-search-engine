import os;
import json;
from py2neo import *;

files = os.listdir(os.getcwd() + '/test');

authenticate("localhost:7474", "neo4j", "prince")
graph = Graph();

data = [];

for f in files:
	data_file = open(os.getcwd() + '/test/' + f);
	data.append(json.load(data_file));
	data_file.close();

tx = graph.begin();

tx.append("MATCH(v) DETACH DELETE v");

for i in range(0,len(data)):
	d = data[i];
	tx.append("CREATE (v:video { _id:'" + str(d['videoInfo']['id']) + "',commentCount:" + str(d['videoInfo']['statistics']['commentCount']) + ", viewCount:" + str(d['videoInfo']['statistics']['viewCount']) + ", favoriteCount:" +  str(d['videoInfo']['statistics']['favoriteCount']) + ", dislikeCount:" + str(d['videoInfo']['statistics']['dislikeCount']) + ", likeCount:" + d['videoInfo']['statistics']['likeCount'] + "})" );


for i in range(0,len(data)-1):
	print(i);
	for j in range(i+1,len(data)):
		if i == j:
			continue;
		same_channel = data[i]['videoInfo']['snippet']['channelId'] == data[j]['videoInfo']['snippet']['channelId'];
		common_tags = 1;
		if 'tags' in data[i]['videoInfo']['snippet'].keys() and 'tags' in data[j]['videoInfo']['snippet'].keys():
			tagsi = data[i]['videoInfo']['snippet']['tags'];
			tagsj = data[j]['videoInfo']['snippet']['tags'];
			[x.lower() for x in tagsi];
			[x.lower() for x in tagsj];
			common_tags = len(set(tagsi).intersection(set(tagsj)));
		else:
			common_tags = 0;
		desci = data[i]['videoInfo']['snippet']['description'].split();
		descj = data[j]['videoInfo']['snippet']['description'].split();
		[x.lower() for x in desci];
		[x.lower() for x in descj];
		common_desc = len(set(desci).intersection(set(descj)));
		if same_channel:
			tx.append("MATCH (v1:video), (v2:video) WHERE v1._id = '" + str(data[i]['videoInfo']['id']) + "' AND v2._id = '" + str(data[j]['videoInfo']['id']) + "' CREATE (v1)-[r1:SAME_CHANNEL]->(v2);");
		
		if common_tags:
			graph.run("MATCH (v1:video), (v2:video) WHERE v1._id = '" + str(data[i]['videoInfo']['id']) + "' AND v2._id = '" + str(data[j]['videoInfo']['id']) + "' CREATE (v1)-[r2:COMMON_TAGS {weight:" + str(common_tags) + "}]->(v2);");
			tx.append("MATCH (v1:video), (v2:video) WHERE v1._id = '" + str(data[i]['videoInfo']['id']) + "' AND v2._id = '" + str(data[j]['videoInfo']['id']) + "' CREATE (v1)-[r2:COMMON_TAGS {weight:" + str(common_tags) + "}]->(v2);");
		
		if common_desc:
			tx.append("MATCH (v1:video), (v2:video) WHERE v1._id = '" + str(data[i]['videoInfo']['id']) + "' AND v2._id = '" + str(data[j]['videoInfo']['id']) + "' CREATE (v1)-[r3:COMMON_DESC {weight:" + str(common_desc) + "}]->(v2);");

		tx.append("MATCH (v1:video), (v2:video) WHERE v1._id = '" + str(data[i]['videoInfo']['id']) + "' AND v2._id = '" + str(data[j]['videoInfo']['id']) + "' CREATE (v1)-[r4:SAME_SESSION {weight:" + "0" + "}]->(v2);");
	
tx.process();
tx.commit();