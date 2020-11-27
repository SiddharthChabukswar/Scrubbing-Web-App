import sys
import csv
import os
import gc
import shutil

from dbconnect import connection
from datetime import datetime

class GenerateReports:
	
	def __init__(self, list_id, username):
		self.list_id = list_id
		timestamp = datetime.now().replace(microsecond=0)
		date = timestamp.date()
		time = timestamp.time()
		self.dirname = f"Reports/Reports_{list_id}_{username}_{date}_{time.hour}_{time.minute}_{time.second}"
		dirpath = self.dirname
		try:
			if os.path.exists(dirpath) == False and os.path.isdir(dirpath) == False:
				# print("Creating Directory "+dirpath+" ...")
				os.mkdir(dirpath)
				os.chmod(dirpath, 0o777)
				# print("Directory created Successfully.")
			else:
				pass
				# print("Directory "+dirpath+" already exists!")
		except Exception as err:
			print(f"Can't create directory: {dirpath} as {err}")
			sys.exit(1)
		self.header = ['lead_id', 'called_time', 'first_name', 'last_name', 'phone_code', 'phone_number', 'list_id', 'sentence1', 'sentence2', 'status', 'recorded1', 'recorded2']

	def generate(self):
		dirpath = self.dirname
		header = self.header
		list_id = self.list_id

		cur, con = connection('asterisk')

		cur.execute("SELECT * FROM ravenn_auto_dial WHERE status='Y' and list_id = %s", [list_id])
		result = cur.fetchall()
		fp = open(dirpath+'/Positive.csv', 'w')
		myFile = csv.writer(fp)
		myFile.writerow(header)
		myFile.writerows(result)
		fp.close()

		cur.execute("SELECT * FROM ravenn_auto_dial WHERE status='N' and list_id = %s", [list_id])
		result = cur.fetchall()
		fp = open(dirpath+'/Negative.csv', 'w')
		myFile = csv.writer(fp)
		myFile.writerow(header)
		myFile.writerows(result)
		fp.close()

		cur.execute("SELECT * FROM ravenn_auto_dial WHERE status='AM' and list_id = %s", [list_id])
		result = cur.fetchall()
		fp = open(dirpath+'/AnsweringMachine.csv', 'w')
		myFile = csv.writer(fp)
		myFile.writerow(header)
		myFile.writerows(result)
		fp.close()

		cur.execute("SELECT * FROM ravenn_auto_dial WHERE status='U' and list_id = %s", [list_id])
		result = cur.fetchall()
		fp = open(dirpath+'/Unidentified.csv', 'w')
		myFile = csv.writer(fp)
		myFile.writerow(header)
		myFile.writerows(result)
		fp.close()

		cur.execute("SELECT * FROM ravenn_auto_dial WHERE status='NA' and list_id = %s", [list_id])
		result = cur.fetchall()
		fp = open(dirpath+'/NotMarked.csv', 'w')
		myFile = csv.writer(fp)
		myFile.writerow(header)
		myFile.writerows(result)
		fp.close()
		shutil.make_archive(dirpath, 'zip', dirpath)
		if os.path.exists(dirpath) and os.path.isdir(dirpath):
			shutil.rmtree(dirpath)
		con.close()
		gc.collect()
		return dirpath