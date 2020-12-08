import MySQLdb

def connection(db):
	conn = MySQLdb.connect(host='localhost', user='scrubbing_dev', passwd='123456789', db=db)
	cursor = conn.cursor()
	return cursor, conn
