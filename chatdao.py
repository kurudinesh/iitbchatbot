# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import os

import sqlalchemy

logger = logging.getLogger()
# logger.disabled = True
logger.setLevel(logging.FATAL)
def init_connection_engine():
    db_config = {
        # [START cloud_sql_mysql_sqlalchemy_limit]
        # Pool size is the maximum number of permanent connections to keep.
        "pool_size": 5,
        # Temporarily exceeds the set pool_size if no connections are available.
        "max_overflow": 2,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # [END cloud_sql_mysql_sqlalchemy_limit]

        # [START cloud_sql_mysql_sqlalchemy_backoff]
        # SQLAlchemy automatically uses delays between failed connection attempts,
        # but provides no arguments for configuration.
        # [END cloud_sql_mysql_sqlalchemy_backoff]

        # [START cloud_sql_mysql_sqlalchemy_timeout]
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        "pool_timeout": 30,  # 30 seconds
        # [END cloud_sql_mysql_sqlalchemy_timeout]

        # [START cloud_sql_mysql_sqlalchemy_lifetime]
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # reestablished
        "pool_recycle": 1800,  # 30 minutes
        # [END cloud_sql_mysql_sqlalchemy_lifetime]

    }

    if os.environ.get("DB_HOST"):
        return init_tcp_connection_engine(db_config)
    else:
        return init_unix_connection_engine(db_config)


def init_tcp_connection_engine(db_config):
    # [START cloud_sql_mysql_sqlalchemy_create_tcp]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_host = os.environ["DB_HOST"]

    # Extract host and port from db_host
    host_args = db_host.split(":")
    db_hostname, db_port = host_args[0], int(host_args[1])

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            host=db_hostname,  # e.g. "127.0.0.1"
            port=db_port,  # e.g. 3306
            database=db_name,  # e.g. "my-database-name"
        ),
        **db_config
    )
    # [END cloud_sql_mysql_sqlalchemy_create_tcp]

    return pool


def init_unix_connection_engine(db_config):
    # [START cloud_sql_mysql_sqlalchemy_create_socket]
    # Remember - storing secrets in plaintext is potentially unsafe. Consider using
    # something like https://cloud.google.com/secret-manager/docs/overview to help keep
    # secrets secret.
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
    cloud_sql_connection_name = os.environ["CLOUD_SQL_CONNECTION_NAME"]

    pool = sqlalchemy.create_engine(
        # Equivalent URL:
        # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=db_user,  # e.g. "my-database-user"
            password=db_pass,  # e.g. "my-database-password"
            database=db_name,  # e.g. "my-database-name"
            query={
                "unix_socket": "{}/{}".format(
                    db_socket_dir,  # e.g. "/cloudsql"
                    cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
            }
        ),
        **db_config
    )
    # [END cloud_sql_mysql_sqlalchemy_create_socket]

    return pool


# This global variable is declared with a value of `None`, instead of calling
# `init_connection_engine()` immediately, to simplify testing. In general, it
# is safe to initialize your database connection pool when your script starts
# -- there is no need to wait for the first request.
db = None


def create_tables():
    global db
    db = db or init_connection_engine()
    # Create tables (if they don't already exist)
    with db.connect() as conn:
        conn.execute(
           'CREATE TABLE IF NOT EXISTS users (usrname VARCHAR(255), '
           'userid int, status TINYINT, nonmembermsgs '
           'INT default 0, PRIMARY KEY(userid)); ')
        conn.execute(
            'CREATE TABLE IF NOT EXISTS chatlogs (messageid INT AUTO_INCREMENT PRIMARY KEY,'
            ' username VARBINARY(255), t1  TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
        )
        conn.execute(
            'CREATE TABLE IF NOT EXISTS chataccesslogs (accessid INT AUTO_INCREMENT PRIMARY KEY,'
            ' mid INT, t1  TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
        )

        with db.connect() as conn:
            stmt = sqlalchemy.text(
                "SELECT * FROM information_schema.statistics" 
                " WHERE table_schema = 'confession'"
                " AND table_name = 'users' AND column_name = 'status'"
            )
            # Count number of votes for tabs
            user_result = conn.execute(stmt).fetchone()

            if user_result == None:
                conn.execute(
                    'CREATE INDEX statususers'
                    ' ON users (status);')
    print('table creations done')


def get_user(userid):
    votes = []
    with db.connect() as conn:
        stmt = sqlalchemy.text(
            "SELECT status, nonmembermsgs FROM users " "where userid=:userid"
        )
        # Count number of votes for tabs
        user_result = conn.execute(stmt, userid=userid).one_or_none()

        if user_result != None:
            return {"status":user_result[0],"nnmsgs":user_result[1]}
    return None

def loaduserids():
    global db
    with db.connect() as conn:
        recent_votes = conn.execute(
            "SELECT userid FROM users where status=1;"
        ).fetchall()
        # Convert the results into a list of dicts representing votes
        userids = set()
        for row in recent_votes:
            userids.add(int(row[0]))
        return userids

def save_user(user):
    global db
    # Get the team and time the vote was cast.
    time_cast = datetime.datetime.utcnow()

    # Preparing a statement before hand can help protect against injections.
    # status 1 active, status 2 left, status 3 ban
    stmt = sqlalchemy.text(
        'REPLACE INTO users (usrname, userid, status, nonmembermsgs )'
        '  VALUES (:usrname, :userid, :status, :nonmembermsgs)'
    )
    try:
        # Using a with statement ensures that the connection is always released
        # back into the pool at the end of statement (even if an error occurs)
        with db.connect() as conn:
            conn.execute(stmt, usrname=user[0], userid=user[1], status=user[2], nonmembermsgs=user[3])
    except Exception as e:
        # If something goes wrong, handle the error in this section. This might
        # involve retrying or adjusting parameters depending on the situation.
        # [START_EXCLUDE]
        print(e)

def update_user_status(userid, status):
    global db
    stmt = sqlalchemy.text(
        'UPDATE users set  status=:status'
        '  where userid=:userid'
    )
    try:
        with db.connect() as conn:
            conn.execute(stmt, status=status, userid=userid)
    except Exception as e:
        print(e)

def update_user_msgcount(userid):
    global db
    stmt = sqlalchemy.text(
        'UPDATE users set  nonmembermsgs=nonmembermsgs+1'
        '  where userid=:userid'
    )
    try:
        with db.connect() as conn:
            conn.execute(stmt, userid=userid)
    except Exception as e:
        print(e)

def save_log(username):
    global db
    # Get the team and time the vote was cast.
    time_cast = datetime.datetime.utcnow()

    # Preparing a statement before hand can help protect against injections.
    stmt = sqlalchemy.text(
        'INSERT INTO chatlogs (username)'
        '  VALUES (:username)'
    )
    try:
        # Using a with statement ensures that the connection is always released
        # back into the pool at the end of statement (even if an error occurs)
        with db.connect() as conn:
            result = conn.execute(stmt, username=username)
            new_id = result.lastrowid
            return new_id
    except Exception as e:
        # If something goes wrong, handle the error in this section. This might
        # involve retrying or adjusting parameters depending on the situation.
        # [START_EXCLUDE]
        print(e)

def save_log_access(mid):
    global db
    # Preparing a statement before hand can help protect against injections.
    stmt = sqlalchemy.text(
        'INSERT INTO chataccesslogs (mid)'
        '  VALUES (:mid)'
    )
    try:
        with db.connect() as conn:
            result = conn.execute(stmt, mid=mid)
            new_id = result.lastrowid
            return new_id
    except Exception as e:
        print(e)
    return -1

def get_log(mid):
    global db
    votes = []
    with db.connect() as conn:
        stmt = sqlalchemy.text(
            "SELECT username FROM chatlogs " "where messageid=:messageid"
        )
        # Count number of votes for tabs
        user_result = conn.execute(stmt, messageid=mid).fetchone()

        if user_result != None:
            return user_result[0]
    return None

def getaccesslogs(startat,perpage):
    global db
    with db.connect() as conn:
        recent_votes = conn.execute(
            "SELECT * FROM chataccesslogs order by t1 desc limit %s, %s;", (startat,perpage)
        ).fetchall()
        # Convert the results into a list of dicts representing votes
        # userids = set()
        # for row in recent_votes:
        #     userids.add(int(row[0]))
        return recent_votes

def getlogscount():
    global db
    with db.connect() as conn:
        recent_votes = conn.execute(
            "SELECT count(*) FROM chataccesslogs"
        ).fetchone()
        # Convert the results into a list of dicts representing votes
        # userids = set()
        # for row in recent_votes:
        #     userids.add(int(row[0]))
        return int(recent_votes[0])
