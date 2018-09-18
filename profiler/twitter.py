from . import profiler
from tools.twitter_scraper import get_tweets
import uuid

class TwitterProfiler(profiler.Profiler):

    def __init__(self):
        """
        TwitterProfiler initialization
        """
        
        profiler.Profiler.__init__(self)
        self.type = self.__class__.__name__

    def query(self, twitter_handle):
        """
        query twitter for the provided twitter handle
        example: @realDonaldTrump
        """
        query_uuid = str(uuid.uuid4())
        count = 0
        result = []
        for tweet in get_tweets(twitter_handle):
            if tweet is None:
                continue
            # get relevant data from tweet
            metadata = dict()
            metadata["date"] = tweet["date"]
            # metadata["replies"] = tweet["replies"]
            # metadata["retweets"] = tweet["retweets"]
            # metadata["likes"] = tweet["likes"]
            metadata["tweet_id"] = tweet["tweetId"]
            # metadata["photos"] = [ photo for photo in tweet["entries"]["photos"] ]
            metadata["urls"] = [ url for url in tweet["links"] ]
            metadata["hashtags"] = [ hashtag for hashtag in tweet["hashtags"] ]
            # metadata["videos"] = [ video for video in tweet["entries"]["videos"] ]
            metadata["retweet"] = tweet["retweet"]
            metadata["username"] = tweet["username"]
            metadata["fullname"] = tweet["fullname"]
            content = tweet["text"]

            count += 1

            # store tweet_activity in database
            tweet_activity = profiler.Activity(query_uuid, self.type, metadata, content)
            self.store(tweet_activity)
            result.append(tweet_activity)

        # store query to database
        self.store_query(query_uuid, twitter_handle, count)

        return result



