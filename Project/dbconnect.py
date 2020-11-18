import MySQLdb

def connection():
	conn = MySQLdb.connect(host='localhost', user='scrubbing_dev', passwd='123456789', db='scrubbing')
	cursor = conn.cursor()
	return cursor, conn