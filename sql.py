import pymysql


def clicked(user_id, video_id):
	db = pymysql.connect("localhost","root","pass","VIDEOS" )
	cursor = db.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS clicks (user_id " + "VARCHAR(255), video_id VARCHAR(255), clicks INT);")
	cursor.execute("SELECT clicks FROM clicks WHERE user_id = '" + user_id + "' AND video_id = '" + video_id + "';")
	results = cursor.fetchall()
	if len(results)==0:
		query = "INSERT INTO clicks(user_id, video_id, clicks) VALUES ('" + user_id + "', '" + video_id + "', '" + "1" + "' );"
		cursor.execute(query)
		print("1")
	else:
		query = "UPDATE clicks SET clicks = clicks + 1 WHERE user_id = '" + user_id + "' AND video_id = '" + video_id + "' ;" 
		cursor.execute(query)
		print("2")
	db.commit()
	db.close()

#def refresh_trending_videos():
	

#def get_trending_videos():
