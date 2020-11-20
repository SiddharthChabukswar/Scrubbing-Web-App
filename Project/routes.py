import gc
import math

from flask import Flask, render_template, request, url_for, redirect, session
from dbconnect import connection
from MySQLdb import escape_string
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.secret_key = "HelloworlditsPython"


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
		return False, (), 1
	if page > possible_pages:
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
	session['statement'] = ''
	return render_template('home.html')
	

@app.route('/create_job/')
@login_required
def create_job():
	session['statement'] = ''
	return render_template('create_job.html')


@app.route('/delete_job/')
@login_required
def delete_job():
	session['statement'] = ''
	return render_template('delete_job.html')


@app.route('/view_jobs/', defaults={'page':1}, methods = ['GET', 'POST'])
@app.route('/view_jobs/page/<int:page>', methods = ['GET', 'POST'])
@login_required
def view_jobs(page):
	if request.method == 'POST':
		page = 1
		job_number = request.form['job_number']
		list_id = request.form['list_id']
		username = request.form['username']
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		planned_call_date = request.form['planned_call_date']
		status = request.form['status']
		print(job_number, list_id, username, first_name, last_name, planned_call_date, status)
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
		print(statement)
		session['statement'] = statement
		flag, data, possible_pages = view_jobs_helper(statement, page)
		if flag == True:
			session['statement'] = ''
			return redirect(url_for('view_jobs'))
		else:
			return render_template('view_jobs.html', data = reversed(data), possible_pages = possible_pages, current_page = page)
	else:
		statement = session['statement']
		print("statement:: ", statement)
		flag, data, possible_pages = view_jobs_helper(statement, page)
		if flag == True:
			session['statement'] = ''
			return redirect(url_for('view_jobs'))
		else:
			return render_template('view_jobs.html', data = reversed(data), possible_pages = possible_pages, current_page = page)


@app.route('/voice_generator/')
@login_required
def voice_generator():
	session['statement'] = ''
	return render_template('voice_generator.html')


if __name__ == "__main__":
	app.run(debug=True)