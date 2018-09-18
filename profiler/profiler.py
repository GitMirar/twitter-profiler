import configparser
import datetime
import json
import uuid

from . import database

class Activity:

    def __init__(self, query_uuid, activity_type, metadata=None, content=None, activity_uuid=None):
        """
        initialize Activity
        """
        self.metadata = metadata
        self.content = content
        if activity_uuid is None:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = activity_uuid
        self.activity_type = activity_type
        self.query_uuid = query_uuid

    def get_metadata(self):
        """
        returns the metadata of this activity as dict
        """
        return self.metadata

    def get_content(self):
        """
        returns the content of this activity as string
        """
        return self.content

    def get_uuid(self):
        """
        returns the uuid of the activity
        """
        return self.uuid

    def get_activity_type(self):
        """
        returns the activity type as string
        """
        return self.activity_type

    def get_query_uuid(self):
        """
        returns query uuid
        """
        return self.query_uuid

    def get_urls(self):
        """
        return urls
        """
        if not "urls" in self.metadata:
            return []
        return self.metadata["urls"]

    def get_date(self):
        """
        return timestamp of activity
        """
        if not "date" in self.metadata:
            return None
        return self.metadata["date"]

class Profiler:

    CONFIG_FILE = "profiler.ini"
    # 7 day cache threshhold
    CASH_THRESH_DAYS = 7
    # use cache only if more than cached results are available
    CASH_THRESH_N = 10

    def __init__(self, database_backend=None):
        """
        initialize Profiler base class
        """

        # parse config file
        self.config_parser = configparser.ConfigParser()
        self.config_parser.read(self.CONFIG_FILE)
        self.config = dict()

        for section in self.config_parser.sections():

            if not section in self.config:
                self.config[section] = dict()

            for option in self.config_parser[section]:
                value = self.config_parser[section][option]
                self.config[section][option] = value

        if database_backend is None:
            # default to SQLi database backend if no interface is provided
            self.database_backend = database.SQLiInterface()
        else:
            self.database_backend = database_backend

        self.type = self.__class__.__name__

    def store(self, my_activity):
        """
        store activity in database
        """
        # store activity in database
        self.database_backend.store(my_activity)

    def store_query(self, query_uuid, query, result_count):
        """
        store query in database
        """
        self.database_backend.store_query(query_uuid, self.type, query, result_count)

    def query(self, qry):
        """
        perform a query
        """
        return []

    def query_cached(self, qry):
        """
        perform a cached query
        use cached results if available
        """
        now = datetime.datetime.utcnow()
        queries = self.database_backend.get_queries_by_query_and_type(qry, self.type)
        use_cache = False
        for query in reversed(queries):
            d = datetime.datetime.fromisoformat(query[1])
            if (now - d).days < self.CASH_THRESH_DAYS:
                # we got a fresh query, checking for # of results now
                if query[2] > self.CASH_THRESH_N:
                    use_cache = True
                    query_uuid = query[0]
                    activity_type = query[3]
                    break

        if not use_cache:
            # no fresh results available, perform query
            return self.query(qry)

        result = []
        db_activities = self.database_backend.get_activities_by_query_uuid(query_uuid)
        for db_activity in db_activities:
            result.append(Activity(query_uuid, activity_type, json.loads(db_activity[2]), db_activity[3], db_activity[0]))

        return result

