import os
import requests

from flask import Flask, flash, jsonify, render_template, redirect, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, get_book


app = Flask(__name__)

# Check for environment variable for database
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Check for environment varible for Goodreads API
if not os.getenv("GOODREADS_KEY"):
    raise RuntimeError("GOODREADS_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Ask for Goodreads Key
gr = os.getenv("GOODREADS_KEY")
goodreads_key = scoped_session(sessionmaker(bind=gr))


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


@app.route('/book/<isbn_num>', methods=('POST',))
def book(isbn_num):

    # Ensure that user reached route via POST
    if request.method != 'POST':
        abort(405, "You can't reach this route with GET request!")

    # Use helper function `get_book()` to store results in book
    book = get_book(isbn_num)

    # Use Goodreads API https://www.goodreads.com/api
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreads_key, "isbns": isbn_num})
    res_json = (res.json()['books'][0])

    return render_template('book.html', book = book, book_json = res_json)


@app.route('/prowebinar', methods=['GET', 'POST'])
def prowebinar():
    # Passed the access_token through return_from_oauth form
    auth_access_token = request.form.get('access_token')
    organizer_key = request.form.get('organizer_key')
    return render_template('prowebinar.html', auth_access_token=auth_access_token, organizer_key=organizer_key)


@app.route('/create_webinar', methods=['GET', 'POST'])
def create_webinar():
    if request.method == 'POST':
        auth_access_token = request.form.get('authAccessToken')
        organizer_key = request.form.get('organizer_key')
        subject = request.form.get('create_subject')
        description = request.form.get('create_description')
        startDate = request.form.get('create_startDate')
        endDate = request.form.get('create_endDate')
        startTime = request.form.get('create_startTime')
        endTime = request.form.get('create_endTime')

        startDateTime = startDate + 'T' + startTime + ':00Z'
        endDateTime = endDate + 'T' + endTime + ':00Z'

        url = 'https://api.getgo.com/G2W/rest/v2/organizers/' + organizer_key + '/webinars'

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': auth_access_token,
        }

        data = '{\n"subject": "' + subject + '",\n"description": "' + description + '",\n"times": [\n{\n"startTime": "' + startDateTime + '", \n"endTime": "' + endDateTime + '"\n}\n],\n"timeZone": "GMT+01:00",\n"type": "single_session"\n}'

        response = requests.post(url, headers=headers, data=data)
        print(response)
        print(response.json())
        res = response.json()

        return render_template('create_webinar.html', response=res)

    else:
        return render_template('create_webinar.html')


@app.route('/get_webinars')
def get_webinars():
    headers = {
        'Accept': 'application/json',
        'Authorization': 'O0KAMlUisOiG9eqyfLyVlpQG9lOv',
    }

    params = (
        ('fromTime', '2018-07-13T10:00:00Z'),
        ('toTime', '2018-12-30T23:59:00Z'),
        ('size', '100'),
    )

    response = requests.get('https://api.getgo.com/G2W/rest/v2/accounts/4564227092871728645/webinars', headers=headers, params=params)
    res = (response.json())['_embedded']['webinars']

    return render_template('get_webinars.html', response=res)


@app.route('/add_registrant')
def add_registrant():
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.citrix.g2wapi-v1.1+json',
    'Authorization': 'nLUXYfKueLy3PAINr4qd5WWWY6jL',
    }

    params = (
        ('resendConfirmation', 'false'),
    )

    data = '{\n  "firstName": "John",\n  "lastName": "Doe",\n  "email": "johndoe@test.com",\n  "organization": "Company that doesn\'t exist",\n  "jobTitle": "Manager",\n}'

    response = requests.post('https://api.getgo.com/G2W/rest/v2/organizers/3793328697070057484/webinars/687419462163600653/registrants', headers=headers, params=params, data=data)
    print(response.json())
    res = response.json()

    return render_template('add_registrant.html', response=res)


@app.route('/return/from/oauth')
def return_from_oauth():

    # Get the code returned from oAuth to pass it into post request
    oauth_code = request.args.get('code')
    # print(request.args.get('code'))
    # print oauth_code

    headers = {
    'Authorization': 'Basic aXRGZHlKVFExMzdHallHbENMNUViN1BBSUpQSTBOODE6emRyR3JLWHZ3cEo5UGRSTg==',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
      'grant_type': 'authorization_code',
      'code': oauth_code,
      'redirect_uri': 'http://127.0.0.1:5000/return/from/oauth'
    }

    response = requests.post('https://api.getgo.com/oauth/v2/token', headers=headers, data=data)
    res = response.json()

    flash('Successfully authenticated!')

    return render_template('return_from_oauth.html', response = res)


@app.route('/prowebinar/getme')
def getme():

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer 0RBV6ayAA9AgGQ0t5GS2de6xytqT',
    }

    response = requests.get('https://api.getgo.com/admin/rest/v1/me', headers=headers)

    res = response.json()
    print(res)

    return render_template('prowebinar_getme.html', response = res)
