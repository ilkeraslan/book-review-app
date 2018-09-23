import os

from flask import Flask, flash, jsonify, render_template, redirect, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register user"""

    # User reached route via POST
    if request.method == 'POST':

        # Ensure username was submitted
        if not request.form.get('username'):
            flash('You must provide a username.')
            return redirect(url_for('register'))

        # Ensure password was submitted
        if not request.form.get('password'):
            flash('You must provide a password.')
            return redirect(url_for('register'))

        # Query database for username
        username = request.form.get('username')
        rows = db.execute('SELECT * FROM users WHERE username = :username', {"username": username}).fetchall()
        # Check if it exists
        if len(rows) != 0:
            flash('This username exists.')
            return redirect(url_for('register'))
        # Insert values provided to database
        password = generate_password_hash(request.form.get('password'))
        db.execute('INSERT INTO users (username, password) VALUES (:username, :password)', {"username": username, "password": password})
        print(f"User {username} has been registered correctly.")
        # Commit changes
        db.commit()

        # Remember username for that session
        session['username'] = request.form['username']
        flash('Successfully registered.')
        return redirect(url_for('index'))

    # User reached route via GET
    else:
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log user in"""

    # Forget any username
    session.clear()

    # User has reached via POST
    if request.method == 'POST':

        # Ensure username was submitted
        if not request.form.get('username'):
            flash('You must provide a username.')
            return redirect(url_for('login'))

        # Ensure password was submitted
        if not request.form.get('password'):
            flash('You must provide a password.')
            return redirect(url_for('login'))

        # Query db for that username
        username = request.form.get('username')
        rows = db.execute('SELECT * FROM users WHERE username = :username', {"username": username}).fetchall()

        # Check if rows has some data
        if len(rows) == 0:
            flash('No such username.')
            return redirect(url_for('login'))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get('password')):
            flash('Wrong password.')
            return redirect(url_for('login'))

        # Remember username for that session
        session['username'] = request.form['username']

        # Redirect with success message
        flash('Successfully logged in!')
        return redirect(url_for('index'))

    # User reached route via GET
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    """Log user out"""

    # Forget any username
    session.clear()

    # Redirect to index page
    flash("Successfully logged out!")
    return redirect(url_for('index'))


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Enable the user to search ISBN, title or author of a book and show results."""

    # User reached route via POST
    if request.method == 'POST':
        isbnQuery = request.form.get('isbnQuery')
        titleQuery = request.form.get('titleQuery')
        authorQuery = request.form.get('authorQuery')

        # Query db
        rows = db.execute('SELECT * FROM books WHERE isbn = :isbn OR author = :author OR title = :title', {"isbn": isbnQuery, "author": authorQuery, "title": titleQuery})
        print(rows)

        bookQueryResults = [{'isbnResult': isbnQuery, 'titleResult': titleQuery, 'authorResult': authorQuery}]
        # for key, value in bookQueryResults.items():
        #     print(key, value)

        return render_template('search.html', bookQueryResults = bookQueryResults)

    # User reached route via GET
    else:
        return render_template('search.html')
