import os
import requests

from flask import Flask, session, render_template, redirect, url_for, flash, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from math import ceil

app = Flask(__name__)

api_key = "imWC7V9VPwQMsGykwuJEA"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
	DB_URL = "postgresql://postgres:c90d@localhost:5432/project1"
	#raise RuntimeError("DATABASE_URL is not set")
else:
	DB_URL = os.getenv("DATABASE_URL")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



# Set up database
engine = create_engine(DB_URL)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
	return render_template("index.html")

@app.route("/search.html")
def search():
	query = request.args['search']
	db_query = '%' + request.args['search'] + '%'
	try:
		page = int(request.args['page'])
	except:
		page = 1
	search_results = db.execute('SELECT * FROM books WHERE \
		isbn ILIKE :query OR title ILIKE :query OR author ILIKE :query', 
		{'query': db_query}).fetchall()
	max_page = ceil(len(search_results)/10)
	return render_template("search.html", search_results=search_results,
	 page=page, max_page=max_page, query=query)

@app.route("/book/<int:book_id>")
def book(book_id):
	book = db.execute('SELECT id, isbn, title, author, year FROM books WHERE \
		id = :book_id', {'book_id': book_id}).fetchone()
	if book != None:	
		try:
			res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key, "isbns": book.isbn})
			res = res.json()
		except:
			res = None
		reviews = db.execute('SELECT user_id, rating, message, username FROM reviews \
		 JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id', {'book_id': book_id}).fetchall()
		return render_template("book.html", book=book, gr=res, reviews=reviews)
	else:
		return redirect(url_for('index'))

@app.route("/register.html", methods=['GET', 'POST'])
def register():
	if session.get('logged_in'):
		return redirect(url_for('index'))

	if request.method == 'POST':
		username = request.form['username'].lower()
		password = request.form['password']
		error = None

		if not username:
			error = 'Username is required'
		elif not password:
			error = 'Password is required'
		elif db.execute('SELECT id FROM users WHERE username = :username'
			, {'username':username}).fetchone() is not None:
			error = 'User {} is already registered.'.format(username)

		if error is None:
			db.execute(
				'INSERT INTO users (username, password) VALUES (:username, :password)',
				{'username':username, 'password':generate_password_hash(password)}
			)
			db.commit()
			return redirect(url_for('login'))

		flash(error)

	return render_template("/auth/register.html")

@app.route("/login.html", methods=['GET', 'POST'])
def login():
	if session.get('logged_in'):
		return redirect(url_for('index'))

	if request.method == 'POST':
		username = request.form['username'].lower()
		password = request.form['password']
		error = None

		user = db.execute(
			'SELECT * FROM users WHERE username = :username', {'username':username}
		).fetchone()

		if user is None:
			error = 'Incorrect username.'
		elif not check_password_hash(user['password'], password):
			error = 'Incorrect password.'

		if error is None:
			session.clear()
			session['user_id'] = user['id']
			session['logged_in'] = True
			return redirect(url_for('index'))

		flash(error)

	return render_template("/auth/login.html")

@app.route("/logout.html")
def logout():
	session.clear()
	return redirect(url_for('index'))

@app.route("/review/<int:book_id>", methods=['POST'])
def review(book_id):
	try:
		rating = request.form['stars']
	except:
		rating = None
	error = None
	message = request.form['text']
	try:
		user_id = session['user_id']
	except:
		error= "Please login first"
	if not rating:
		error = "Insert a star rating"
	elif rating not in ['1','2','3','4','5']:
		error = "Insert valid rating"
	elif not error:
		db.execute('INSERT INTO reviews (book_id, user_id, rating, message) \
	 	VALUES (:book_id, :user_id, :rating, :message)',
	  	{'book_id':book_id, 'user_id':user_id, 'rating':rating, 'message':message})
		db.commit()
		return redirect(f"{url_for('book', book_id=book_id)}")
	flash(error)
	return redirect(f"{url_for('book', book_id=book_id)}")
