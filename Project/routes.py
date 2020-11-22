import gc
import math

from flask import Flask, render_template, request, url_for, redirect, session
from dbconnect import connection
from MySQLdb import escape_string
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import timedelta, datetime


##########################################################################################################################################################################################


app = Flask(__name__)
app.secret_key = "HelloworlditsPython"


##########################################################################################################################################################################################


def login_required(func):
	@wraps(func)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return func(*args, **kwargs)
		else:
			return redirect(url_for('login'))
	return wrap

def view_jobs_helper(statement, page):
	perpage = 7
	cur, con = connection('scrubbing')
	cur.execute("SELECT count(*) FROM Schedules" + statement +";")
	totalelements = int(cur.fetchall()[0][0])
	possible_pages = math.ceil(float(totalelements/perpage))
	if possible_pages == 0:
		con.close()
		gc.collect()
		return False, (), 1
	if page > possible_pages:
		con.close()
		gc.collect()
		return True, (), possible_pages
	currentpage = (totalelements - (perpage*page))
	if currentpage < 0:
		perpage = perpage + currentpage
		currentpage = 0
	# print(totalelements, perpage, currentpage, page)
	cur.execute("SELECT * FROM Schedules"+ statement +" LIMIT %s OFFSET %s",[perpage, currentpage])
	data = cur.fetchall()
	# for d in data:
	# 	print(d)
	con.close()
	gc.collect()
	return False, data, possible_pages

def delete_job_helper(job_number):
	error = 'job deletion failed'
	cur, con = connection('scrubbing')
	cur.execute("SELECT * FROM Schedules WHERE job_number >= %s", [job_number])
	alldata = cur.fetchall()
	currdata = alldata[0]
	alldata = alldata[1:]
	all_data_list = []
	for i in alldata:
		all_data_list.append(list(i))
	alldata = all_data_list	
	new_start_datetime = currdata[7]
	new_end_datetime = ''
	for i in range(0, len(alldata)):
		timediff = alldata[i][8] - alldata[i][7]
		new_end_datetime = new_start_datetime + timediff
		alldata[i][7] = new_start_datetime
		alldata[i][8] = new_end_datetime
		new_start_datetime = new_end_datetime + timedelta(minutes=30)
	for i in range(0, len(alldata)):
		cur.execute("UPDATE Schedules SET job_start_time = %s, job_expected_end_time = %s WHERE job_number = %s", [alldata[i][7], alldata[i][8], alldata[i][0]])
	cur.execute("DELETE FROM Schedules WHERE job_number = %s;", [job_number])
	con.commit()
	con.close()
	gc.collect()
	error = 'job deleted successfully'
	return error

def check_list_present(list_id):
	count = 0
	cur, con = connection('asterisk')
	cur.execute("SELECT list_id FROM vicidial_lists WHERE list_id = %s", [list_id])
	data = cur.fetchall()
	count = len(data)
	con.close()
	gc.collect
	return count

def check_lead_count(list_id):
	count = 0
	cur, con = connection('asterisk')
	cur.execute("SELECT count(*) FROM vicidial_list WHERE list_id = %s", [list_id])
	count = cur.fetchall()[0][0]
	con.close()
	gc.collect()
	return count

def next_start_date():
	offset = timedelta(minutes=30)
	cur, con = connection('scrubbing')
	cur.execute("SELECT count(*) FROM Schedules")
	count = cur.fetchall()[0][0] - 1
	if count >= 0:
		cur.execute("SELECT job_expected_end_time FROM Schedules LIMIT 1 OFFSET %s;", [count])
		last_element_date = cur.fetchall()[0][0]
		# print(last_element_date)
		con.close()
		gc.collect()
		if datetime.now() > last_element_date:
			return datetime.now() + offset
		else:
			return last_element_date + offset
	else:
		con.close()
		gc.collect()
		return datetime.now() + offset

def estimate_end_date(planned_start_date, lead_count):
	scale = 4
	seconds = lead_count * scale
	offset = timedelta(seconds=seconds)
	return planned_start_date + offset

def check_dates_still_valid(planned_start_date):
	offset = timedelta(minutes=20)
	cur, con = connection('scrubbing')
	cur.execute("SELECT count(*) FROM Schedules")
	count = cur.fetchall()[0][0] - 1
	if count >= 0:
		cur.execute("SELECT job_number, job_expected_end_time FROM Schedules LIMIT 1 OFFSET %s;", [count])
		data = cur.fetchall()
		new_token = data[0][0] + 1
		last_element_date = data[0][1] + offset
		# print(last_element_date)
		con.close()
		gc.collect()
		if last_element_date > planned_start_date:
			return False, 0
		else:
			return True, new_token
	else:
		con.close()
		gc.collect()
		return True, 1

def add_job_helper(job_number):
	username = session['username']
	dbfirstname = session['first_name']
	dblastname = session['last_name']
	list_id = session['list_id']
	job_created = datetime.now()
	planned_call_date = datetime.strptime(session['planned_call_date'], '%Y-%m-%d').date()
	planned_start_date = session['planned_start_date']
	estimated_end_date = session['estimated_end_date']
	# print(planned_call_date, type(planned_call_date))
	# print(planned_start_date, type(planned_start_date))
	status = 'N'
	parameters = [job_number, list_id, username, dbfirstname, dblastname, job_created, planned_call_date, planned_start_date, estimated_end_date, status]
	cur, con = connection('scrubbing')
	cur.execute("INSERT INTO Schedules VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", parameters)
	con.commit()
	con.close()
	gc.collect()

##########################################################################################################################################################################################


@app.route('/login/', methods = ['GET', 'POST'])
def login():
	if 'logged_in' in session:
		return redirect(url_for('home'))
	error = ''
	cur, con = connection('scrubbing')
	if request.method == 'POST':
		username = escape_string(request.form['username'])
		password = escape_string(request.form['password'])
		cur.execute("SELECT * FROM Users where username = %s",[username])
		data = cur.fetchall()
		if len(data) == 0:
			error = 'Invalid Credentials, please try again!'
		else:
			data = data[0]
			dbfirstname = data[1]
			dblastname = data[2]
			dbpassword = data[3]
			con.close()
			gc.collect()
			if sha256_crypt.verify(password, dbpassword) == True:
				session['logged_in'] = True
				session['username'] = username
				session['first_name'] = dbfirstname
				session['last_name'] = dblastname
				session['statement'] = ''
				return redirect(url_for('home'))
			else:
				error = 'Invalid Credentials, please try again!'
	return render_template('login.html', error = error)


@app.route('/logout/')
@login_required
def logout():
	session.clear()
	gc.collect()
	return redirect(url_for('login'))


@app.route('/')
@app.route('/home/')
@login_required
def home():
	session['list_id'] = ''
	session['planned_call_date'] = ''
	session['planned_start_date'] = ''
	session['estimated_end_date'] = ''
	session['del_job_number'] = ''
	session['statement'] = ''
	return render_template('home.html')
	

@app.route('/create_job/', methods = ['GET', 'POST'])
@login_required
def create_job():
	session['del_job_number'] = ''
	session['statement'] = ''
	error = ''
	log = ''
	if request.method == 'POST':
		if request.form['post_type'] == 'Check':
			list_id = request.form['list_id']
			planned_call_date = datetime.strptime(request.form['call_date'], '%Y-%m-%d').date()
			# print(planned_call_date, type(planned_call_date))
			# print(list_id, planned_call_date, datetime.now().date())
			if datetime.now().date() >= planned_call_date:
				error = "Planned date can't be before today!"
				return render_template('create_job.html', error = error)
			list_count = check_list_present(list_id)
			if list_count == 0:
				error = "No list with List_id : " + list_id + " found!"
				return render_template('create_job.html', error = error)
			lead_count = check_lead_count(list_id)
			if lead_count == 0:
				error = "No leads in list with List_id : " + list_id + " found!"
				return render_template('create_job.html', error = error)
			planned_start_date = next_start_date()
			estimated_end_date = estimate_end_date(planned_start_date, lead_count)
			# print(planned_start_date, estimated_end_date)
			session['list_id'] = list_id
			session['planned_call_date'] = str(planned_call_date)
			session['planned_start_date'] = planned_start_date
			session['estimated_end_date'] = estimated_end_date
			return render_template('create_job.html', checked = True, list_id = list_id, lead_count = lead_count, planned_start_date = planned_start_date, estimated_end_date = estimated_end_date)
		elif request.form['post_type'] == 'Yes':
			planned_start_date = session['planned_start_date']
			still_valid, new_token = check_dates_still_valid(planned_start_date)
			if still_valid == True:
				add_job_helper(new_token)
				log = 'Job Added successfully'
				return render_template('create_job.html', log = log, job_number = new_token)
			else:
				error = 'Dates Expired, please try adding again.'
				return render_template('create_job.html', error = error)
		else:
			log = 'Job Addition Cancelled'
			return render_template('create_job.html', log = log)
	else:
		return render_template('create_job.html')


@app.route('/delete_job/', methods = ['GET', 'POST'])
@login_required
def delete_job():
	error = ''
	session['list_id'] = ''
	session['planned_call_date'] = ''
	session['planned_start_date'] = ''
	session['estimated_end_date'] = ''
	session['statement'] = ''
	if request.method == 'POST':
		if request.form['post_type'] == 'Check':
			session['del_job_number'] = ''
			username = session['username'].decode("utf-8")
			job_number = request.form['job_number']
			# print(username, job_number)
			cur, con = connection('scrubbing')
			cur.execute("SELECT * FROM Schedules WHERE job_number = %s AND username = %s AND status = 'N';", (job_number, username))
			data = cur.fetchall()
			con.close()
			gc.collect()
			if len(data) == 0:
				error = 'No Upcoming job with Job Number : ' + job_number + ' found associated with Username: ' + username
				return render_template('delete_job.html', error = error, checked = True)
			else:
				session['del_job_number'] = job_number
				return render_template('delete_job.html', data = data[0], checked = True)
		elif request.form['post_type'] == 'Yes':
			job_number = session['del_job_number']
			error = delete_job_helper(job_number)
			return render_template('delete_job.html', checked = True, error = error)
		else:
			session['del_job_number'] = ''
			error = 'Job deletion cancelled'
			return render_template('delete_job.html', checked = True, error = error)
	else:
		session['del_job_number'] = ''
		return render_template('delete_job.html')


@app.route('/view_jobs/', defaults={'page':1}, methods = ['GET', 'POST'])
@app.route('/view_jobs/page/<int:page>', methods = ['GET', 'POST'])
@login_required
def view_jobs(page):
	session['list_id'] = ''
	session['del_job_number'] = ''
	session['planned_call_date'] = ''
	session['planned_start_date'] = ''
	session['estimated_end_date'] = ''
	if request.method == 'POST':
		page = 1
		job_number = request.form['job_number']
		list_id = request.form['list_id']
		username = request.form['username']
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		planned_call_date = request.form['planned_call_date']
		status = request.form['status']
		# print(job_number, list_id, username, first_name, last_name, planned_call_date, status)
		count = 0
		statement = " WHERE "
		if job_number != '':
			count += 1
			statement += " job_number = '" + str(job_number) + "' AND "
		if list_id != '':
			count += 1
			statement += " list_id = '" + str(list_id) + "' AND "
		if username != '':
			count += 1
			statement += " username = '" + str(username) + "' AND "
		if first_name != '':
			count += 1
			statement += " first_name = '" + str(first_name) + "' AND "
		if last_name != '':
			count += 1
			statement += " last_name = '" + str(last_name) + "' AND "
		if planned_call_date != '':
			count += 1
			statement += " planned_call_date = '" + str(planned_call_date) + "' AND "
		if status != 'All':
			count += 1
			statement += " status = '" + str(status) + "' AND "
		if count == 0:
			statement = ""
		else:
			statement = statement[:len(statement)-5]
		# print(statement)
		session['statement'] = statement
		flag, data, possible_pages = view_jobs_helper(statement, page)
		if flag == True:
			session['statement'] = ''
			return redirect(url_for('view_jobs'))
		else:
			return render_template('view_jobs.html', data = reversed(data), possible_pages = possible_pages, current_page = page)
	else:
		statement = session['statement']
		# print("statement:: ", statement)
		flag, data, possible_pages = view_jobs_helper(statement, page)
		if flag == True:
			session['statement'] = ''
			return redirect(url_for('view_jobs'))
		else:
			return render_template('view_jobs.html', data = reversed(data), possible_pages = possible_pages, current_page = page)


@app.route('/voice_generator/')
@login_required
def voice_generator():
	session['list_id'] = ''
	session['planned_call_date'] = ''
	session['planned_start_date'] = ''
	session['estimated_end_date'] = ''
	session['del_job_number'] = ''
	session['statement'] = ''
	return render_template('voice_generator.html')


if __name__ == "__main__":
	app.run(debug=True)