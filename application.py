import os

from flask import Flask, flash, jsonify, render_template, redirect, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, get_book


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
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
        print('User has been registered correctly.')
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

        # Remember user id for that session
        session['user_id'] = rows[0]['id']

        # Redirect with success message
        flash('Successfully logged in!')
        return redirect(url_for('search'))

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
@login_required
def search():
    """Enable the user to search ISBN, title or author of a book and show results."""

    # User reached route via POST
    if request.method == 'POST':
        isbnQuery = request.form.get('isbnQuery')
        titleQuery = request.form.get('titleQuery')
        authorQuery = request.form.get('authorQuery')

        # Check at least user provides a field for query
        if not isbnQuery and not titleQuery and not authorQuery:
            flash("You should provide at least 1 field.")
            return redirect(url_for('search'))

        # Added '%' wildcards for PostgreSQL ILIKE pattern matching
        # Additional info on: https://www.postgresql.org/docs/9.3/static/functions-matching.html
        if isbnQuery:
            isbnQuery = '%' + isbnQuery + '%'

        if titleQuery:
            titleQuery = '%' + titleQuery + '%'

        if authorQuery:
            authorQuery = '%' + authorQuery + '%'

        # Query db
        rows = db.execute('SELECT * FROM books WHERE isbn ILIKE :isbn OR \
                           author ILIKE :author OR title ILIKE :title LIMIT \
                           10', {"isbn": isbnQuery, "author": authorQuery, \
                           "title": titleQuery}).fetchall()

        # Check if we have any match, if not flash and redirect to search page
        if len(rows) is 0:
            flash("No match. Please search again.")
            return redirect(url_for('search'))

        # Declare a list and for each row append it to that list as a dict object
        bookQueryResults = []
        for row in rows:
            bookQueryResults.append({'isbnResult': row.isbn, 'titleResult': row.title, 'authorResult': row.author})

        return render_template('search.html', bookQueryResults = bookQueryResults)

    # User reached route via GET
    else:
        return render_template('search.html')


@app.route('/book/<isbn_num>')
def book(isbn_num):
    book = get_book(isbn_num)

    return render_template('book.html', book = book)
