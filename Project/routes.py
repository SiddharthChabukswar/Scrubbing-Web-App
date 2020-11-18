import gc

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


@app.route('/login/', methods = ['GET', 'POST'])
def login():
	if 'logged_in' in session:
		return redirect(url_for('home'))
	error = ''
	cur, con = connection()
	if request.method == 'POST':
		username = escape_string(request.form['username'])
		password = escape_string(request.form['password'])
		cur.execute("SELECT * FROM Users where username = %s",[username])
		data = cur.fetchall()
		if len(data) == 0:
			error = 'Invalid Credentials, please try again!'
		else:
			data = data[0]
			print(data)
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
	return render_template('home.html')
	

@app.route('/create_job/')
@login_required
def create_job():
	return render_template('create_job.html')


@app.route('/delete_job/')
@login_required
def delete_job():
	return render_template('delete_job.html')


@app.route('/view_jobs/')
@login_required
def view_jobs():
	return render_template('view_jobs.html')


@app.route('/voice_generator/')
@login_required
def voice_generator():
	return render_template('voice_generator.html')


if __name__ == "__main__":
	app.run(debug=True)