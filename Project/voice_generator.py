import sys
import os
import json
import gc
import numpy as np

from dbconnect import connection
from datetime import datetime
from os.path import join, dirname
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class GenerateVoice:

	def __init__(self, list_id, username, log_number):

		self.list_id = list_id
		self.dirpath = 'out_wav/Leads'
		dirpath = self.dirpath
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

		dirpath = 'out_wav/NPY_Logs'
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
		
		authenticator = IAMAuthenticator('IBM-Key-here')
		self.service = TextToSpeechV1(authenticator=authenticator)
		self.service.set_service_url('IBM-URL-here')
		self.filename = f"{dirpath}/{username}_{list_id}_{log_number}.npy"

	def start(self):
		creation_log = []
		try:
			dirpath = self.dirpath
			service = self.service
			list_id = self.list_id
			cur, con = connection('asterisk')
			cur.execute("SELECT lead_id, phone_code, phone_number, first_name, last_name FROM vicidial_list WHERE list_id = %s", [list_id])
			result = cur.fetchall()
			con.close()
			limit = 1001
			countr = 0
			for row in result:
				lead_id = row[0]
				phone_code = row[1]
				phone_number = row[2]
				first_name = row[3]
				last_name = row[4]
				namefile1 = dirpath+'/'+str(phone_code)+str(phone_number)+'1.wav'
				namefile = dirpath+'/'+str(phone_code)+str(phone_number)+'.wav'
				print(first_name+" "+last_name)
				if os.path.exists(namefile) == False and os.path.isfile(namefile) == False:
					with open(join(dirname(__file__), namefile1), 'wb') as audio_file:
						response = service.synthesize(first_name+' '+last_name, accept='audio/wav', voice="en-US_MichaelV2Voice").get_result()
						audio_file.write(response.content)
					os.system('ffmpeg -loglevel quiet -i '+namefile1+' -ar 8000 '+namefile)
					os.remove(namefile1)
				timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				params = [lead_id, timestamp, first_name, last_name, phone_code, phone_number, list_id, None, None, 'NA', 0, 0]
				creation_log.append(params)
				countr = countr + 1
				if countr == limit:
					break
			creation_log = np.array(creation_log)
			np.save(self.filename, creation_log)
			# print("Created all files Successfully.")
		except Exception as err:
			print(f"Backend Error while making cloud calls: {err}")
			return False
		gc.collect()
		return True

	def write_to_db(self):
		try:
			creation_log = np.load(self.filename, allow_pickle=True)
			cur, con = connection('asterisk')
			for row in creation_log:
				cur.execute("SELECT count(*) FROM ravenn_auto_dial WHERE lead_id=%s",[row[0]])
				if str(cur.fetchall()[0][0]) != '0':
					return False
			for row in creation_log:
				cur.execute("INSERT INTO ravenn_auto_dial VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", row)
				con.commit()
			con.commit()
			con.close()
			os.remove(self.filename)
			gc.collect()
		except Exception as err:
			print(f"Backend Error while writing to db: {err}")
			return False
		return True
	
	
