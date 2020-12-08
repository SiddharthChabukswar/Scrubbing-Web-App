import sys
import csv
import os
import gc
import shutil

from dbconnect import connection
from datetime import datetime

class GenerateLists:

	def __init__(self, list_id, username):
		self.username = username
		self.list_id = list_id
		timestamp = datetime.now().replace(microsecond=0)
		date = timestamp.date()
		time = timestamp.time()
		self.dirname = f"Lists/Lists_{list_id}_{username}_{date}_{time.hour}_{time.minute}_{time.second}"
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
		self.header = ['lead_id', 'list_id', 'gmt_offset_now', 'phone_code', 'phone_number', 'title', 'first_name', 'middle_initial', 'last_name', 'address1', 'address2', 'address3', 'city', 'state', 'province', 'postal_code', 'country_code', 'gender', 'alt_phone', 'email']


	def generate_list(self, status):
		username = self.username
		dirpath = self.dirname
		header = self.header
		list_id = self.list_id

		filename = '/' + username
		for name in status:
			filename = filename + '-' + name
		filename = filename + '.csv'
		fp = open(dirpath+filename, 'w', newline='', encoding='utf-8')
		myFile = csv.writer(fp)
		myFile.writerow(header)

		status_mapper = {
			'positive':'Y',
			'negative':'N',
			'answering_machine':'AM',
			'unidentified':'U',
			'not_marked':'NA'
		}
		actual_status_string = '('
		for name in status:
			actual_status_string += "'"+ status_mapper[name] + "', "
		actual_status_string = actual_status_string[:len(actual_status_string)-2] + ')'
		cur, con = connection('asterisk')
		cur.execute("SELECT lead_id, list_id FROM ravenn_auto_dial WHERE list_id=%s AND status IN " + actual_status_string + ";", [list_id])
		result = cur.fetchall()
		for row in result:
			# print(row)
			lead_id = int(row[0])
			cur.execute("SELECT lead_id, list_id, gmt_offset_now, phone_code, phone_number, title, first_name, middle_initial, last_name, address1, address2, address3, city, state, province, postal_code, country_code, gender, alt_phone, email FROM vicidial_list WHERE list_id=%s and lead_id=%s", [list_id, lead_id])
			result = cur.fetchall()
			if len(result) != 0:
				myFile.writerow(result[0])
		
		fp.close()
		shutil.make_archive(dirpath, 'zip', dirpath)
		if os.path.exists(dirpath) and os.path.isdir(dirpath):
			shutil.rmtree(dirpath)
		con.close()
		gc.collect()
		return dirpath