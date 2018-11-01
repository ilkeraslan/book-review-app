import os

from flask import redirect, request, session, url_for
from functools import wraps
from werkzeug.exceptions import abort
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Helper function to get book info page
def get_book(isbn_num):
    """
    Gets book with provided isbn number.

    """

    # Query db and store the result into book variable
    row = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn_num}).fetchone()

    # If no result, abort with 404 error
    if row is None:
        abort(404, "Book ISBN number {0} not found.".format(isbn_num))

    # Convert it into dict object
    book = {
        'isbn': row.isbn,
        'title': row.title,
        'author': row.author,
        'year': row.year
    }

    return book


#Helper function to verify if a user has commented on a book or not
def userHasCommented(user_id, isbn_num):
    """
    Verifies if a user has commented on a book or not.
    Accepts the id of that user and the isbn number of that book.
    Returns boolean (true/false)
    """
    row = db.execute('SELECT * FROM reviews WHERE (isbn = :isbn) AND  (user_id = :user_id)', {"isbn": isbn_num, "user_id": user_id}).fetchall()

    if len(row) == 0:
        return False
    else:
        return True


# Helper function to get reviews for a specific book
def get_reviews(isbn_num):
    """
    Gets reviews of a book and returns as a dict object
    """
    rows = db.execute('SELECT * FROM reviews WHERE (isbn = :isbn)', {"isbn": isbn_num}).fetchall()
    reviews = []

    # If no review exists, return None
    if len(rows) == 0:
        return None
    else:
        # Push it to list with a foreach loop
        for row in rows:
            reviews.append({
                'review_id': row.review_id,
                'isbn': row.isbn,
                'user_id': row.user_id,
                'username': get_username(row.user_id),
                'rating': row.rating,
                'text_review': row.text_review,
            })
        return reviews


# Helper function to get username
def get_username(user_id):
    """
    Returns username from db
    """
    row = db.execute('SELECT * FROM users WHERE user_id = :user_id', {"user_id": user_id}).fetchone()
    if len(row) is 0:
         username = 'No such user!'
         return username
    else:
        username = row.username
        return username
