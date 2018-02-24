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
```
from sqlalchemy.dialects import registry
registry.register("s3sqlite", "sqlalchemy-s3sqlite.dialect", "S3SQLiteDialect")
```

and change your SQLALCHEMY_DATABASE_URI
```
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 's3sqlite:///quickstart_app.sqlite')
```

At the moment it remains dependent on an environment variable
`S3SQLite_bucket`
to know where to persist the sqlite database. For zappa users, this can be achieved with

```
    "dev": {
        "environment_variables": {
            "S3SQLite_bucket": "mybucketname123"
        }
````
Although I'm open to having a default of the zappa `s3_bucket` if others feel that's a worthwhile improvement. 


# Warnings and future directions

Consistent with the equivalent django code, it assumes databases which are explicitly stored below /tmp/ (or more accurately in a path containing '/tmp/' !) should not be persisted, so
```
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 's3sqlite:////tmp/quickstart_app.sqlite')
```
would not be persisted. However this seems a bit silly since the s3sqlite dialect was explicitly stated. In time it may be worthwhile if this supports the other approaches shown at https://github.com/hkwi/sqlalchemy_gevent


