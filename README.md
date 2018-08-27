# sqlalchemy-s3sqlite
persist a sqlite database in s3, for use with aws lambda

This module allows Flask-User to be used inside AWS Lambda. Normally the sqlite database would randomly disappear between invocations. This module instead makes the database be copied to and from s3 storage as needed. Performance will of course suffer, and having more than one concurrent user is either impossible, or a recipe for nasty surprises, but with it, it's possible to maintain a small site without the comparatively substantial cost of a t2.micro rds or similar.

The idea and implementation borrows heavily from 
https://blog.zappa.io/posts/s3sqlite-a-serverless-relational-database
but that implementation is very django dependent at the moment. Similarly this code still retains some of the rough aspects of that code, such as the repeated use of the hard coded '/tmp'. If it makes sense, I'd welcome having the two codes merge or consolidate in the future.

Usage: based on quickstart_app.py from
https://flask-user.readthedocs.io/en/latest/quickstart_app.html

install the module
```pip install sqlalchemy-s3sqlite```


teach sqlite about s3sqlite 
```python
from sqlalchemy.dialects import registry
registry.register("s3sqlite", "sqlalchemy-s3sqlite.dialect", "S3SQLiteDialect")
```

and change your SQLALCHEMY_DATABASE_URI
```python
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 's3sqlite:///quickstart_app.sqlite')
```

At the moment it remains dependent on an environment variable
`S3SQLite_bucket`
to know where to persist the sqlite database. For zappa users, this can be achieved with

```js
"dev": {
    "environment_variables": {
        "S3SQLite_bucket": "mybucketname123"
    }
}
````
Although I'm open to having a default of the zappa `s3_bucket` if others feel that's a worthwhile improvement. 






# Working Example

```python
# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin
from flask_user import SQLAlchemyAdapter

# Much better to set this via some other mechanism, but this keeps all
#  the settings in this one file
import os
os.environ['S3SQLite_bucket'] = 'MyBucketName'

# this is the important change, it imports sqlalchemy-s3sqlite at runtime
from sqlalchemy.dialects import registry
registry.register("s3sqlite", "sqlalchemy-s3sqlite.dialect", "S3SQLiteDialect")


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///quickstart_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Flask-User QuickStart App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False      # Disable email authentication
    USER_ENABLE_USERNAME = True    # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = False    # Simplify register form


def create_app():
    """ Flask application factory """

    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information
        username = db.Column(db.String(100), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        email_confirmed_at = db.Column(db.DateTime())

        # User information
        first_name = db.Column(db.String(100), nullable=False, server_default='')
        last_name = db.Column(db.String(100), nullable=False, server_default='')

    # Create all database tables
    db.create_all()

    # Setup Flask-User and specify the User data-model
    db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
    user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        # String-based templates
        return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>Home page</h2>
                <p><a href={{ url_for('user.register') }}>Register</a></p>
                <p><a href={{ url_for('user.login') }}>Sign in</a></p>
                <p><a href={{ url_for('home_page') }}>Home page</a> (accessible to anyone)</p>
                <p><a href={{ url_for('member_page') }}>Member page</a> (login required)</p>
                <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
            {% endblock %}
            """)

    # The Members page is only accessible to authenticated users via the @login_required decorator
    @app.route('/members')
    @login_required    # User must be authenticated
    def member_page():
        # String-based templates
        return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>Members page</h2>
                <p><a href={{ url_for('user.register') }}>Register</a></p>
                <p><a href={{ url_for('user.login') }}>Sign in</a></p>
                <p><a href={{ url_for('home_page') }}>Home page</a> (accessible to anyone)</p>
                <p><a href={{ url_for('member_page') }}>Member page</a> (login required)</p>
                <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
            {% endblock %}
            """)

    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

```


# Warnings and future directions

Consistent with the equivalent django code, it assumes databases which are explicitly stored below /tmp/ (or more accurately in a path containing '/tmp/' !) should not be persisted, so
```python
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 's3sqlite:////tmp/quickstart_app.sqlite')
```
would not be persisted. However this seems a bit silly since the s3sqlite dialect was explicitly stated. In time it may be worthwhile if this supports the other approaches shown at https://github.com/hkwi/sqlalchemy_gevent

