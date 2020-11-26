import sys
import os
import json

from dbconnect import connection
from datetime import datetime
from os.path import join, dirname
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class GenerateVoice:

	def __init__(self, list_id):
		self.list_id = list_id
		try:
			dirpath = 'out_wav/Leads'
			if os.path.exists(dirpath) == False and os.path.isdir(dirpath) == False:
				print("Creating Directory "+dirpath+" ...")
				os.mkdir(dirpath)
				os.chmod(dirpath, 0o777)
				print("Directory created Successfully.")
			else:
				print("Directory "+dirpath+" already exists!")
		except Exception as err:
			print(f"Can't create directory: {dirpath} as {err}")
			sys.exit(1)

	def start(self):
		print("Hello!!")
		return
	
	