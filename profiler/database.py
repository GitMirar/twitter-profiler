from . import profiler
import datetime
import sqlite3
import json
import uuid

class DBInterface:

    def __init__(self):
        """
        initialize DBInterface
        """
        pass

    def store(self, activity):
        """
        store a profiler.Activity object in the database
        """
        print(activity)
        pass

    def store_query(self, query_type, query):
        """
        store a query in the database
        """
        pass

    def get_activities_by_query_uuid(self, query_uuid):
        """
        returns a list of all queries matching query_uuid
        """
        pass


class SQLiInterface(DBInterface):

    def __init__(self, database_location=None):
        """
        initialize a SQLi interface
        """
        DBInterface.__init__(self)

        if database_location is None:
            self.database_location = "profiler.sqli"
        else:
            self.database_location = database_location

        with sqlite3.connect(self.database_location) as conn:
            c = conn.cursor()
            # create table for activity data
            c.execute('''CREATE TABLE IF NOT EXISTS activities
                (uuid text, type text, meta text, content text, query_uuid text)''')
            # create table for queries ; used to determine whether
            # cached results should be used
            c.execute('''CREATE TABLE IF NOT EXISTS queries
                (uuid text, date text, results int, type text, query text)''')
            conn.commit()

    def store(self, activity):
        """
        store an activity to the database
        """

        with sqlite3.connect(self.database_location) as conn:
            c = conn.cursor()
            uuid = activity.get_uuid()
            metadata = json.dumps(activity.get_metadata())
            content = activity.get_content()
            activity_type = activity.get_activity_type()
            query_uuid = activity.get_query_uuid()
            c.execute('''INSERT INTO activities
                VALUES (?,?,?,?,?)''', (uuid, activity_type, metadata, content, query_uuid))
            conn.commit()

    def store_query(self, query_uuid, query_type, query, result_count):
        """
        store a query to the database
        """

        with sqlite3.connect(self.database_location) as conn:
            c = conn.cursor()
            date = datetime.datetime.utcnow().isoformat()
            c.execute('''INSERT INTO queries
                VALUES (?,?,?,?,?)''', (query_uuid, date, result_count, query_type, query) )
            conn.commit()

    def get_queries_by_query_and_type(self, query, query_type):
        """
        returns a list of all queries matching query and query_type
        """

        result = []
        with sqlite3.connect(self.database_location) as conn:
            c = conn.cursor()
            c.execute('''SELECT * FROM queries
                WHERE query = ? AND type = ?''', (query, query_type))
            result = c.fetchall()

        return result

    def get_activities_by_query_uuid(self, query_uuid):
        """
        get all results for a query_uuid
        """
        result = []
        with sqlite3.connect(self.database_location) as conn:
            c = conn.cursor()
            c.execute('''SELECT * FROM activities
                WHERE query_uuid = ?''', (query_uuid,))
            result = c.fetchall()

        return result