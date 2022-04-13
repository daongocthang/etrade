import random
import string
from functools import wraps

from flask import session, url_for, redirect

chars = list(string.ascii_letters + string.digits)


def generate_password(num=6):
    random.shuffle(chars)
    password = []
    for i in range(num):
        password.append(random.choice(chars))
    random.choice(password)
    return ''.join(password)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'password' in session:
            return f(*args, **kwargs)
        else:
            print('Invalid Credentials')
            return redirect(url_for('login'))

    return wrap
