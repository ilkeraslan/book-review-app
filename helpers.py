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


def userHasCommented(user_id, isbn_num):
    row = db.execute('SELECT * FROM reviews WHERE (isbn = :isbn) AND  (user_id = :user_id)', {"isbn": isbn_num, "user_id": user_id}).fetchall()

    if len(row) == 0:
        return False
    else:
        return True
