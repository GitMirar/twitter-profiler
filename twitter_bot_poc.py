#!/usr/bin/env python3

import os
import datetime
import sys

from profiler.twitter import TwitterProfiler as TwitterProfiler
from profiler.evaluate import TopicAnalysis, ActivityAnalysis, RetweetAnalysis


def twitter(username):
    text = []
    t = TwitterProfiler()
    activities = t.query_cached(username)
    if activities is None or len(activities) < 20:
        return None
    topics_analysis = TopicAnalysis()
    topics_analysis.add_activity_list(activities)
    topics = topics_analysis.evaluate()
    text.append(f'{username} tweets about "{topics[0].replace(" ", ", ")}"')
    
    retweet_analysis = RetweetAnalysis()
    retweet_analysis.add_activity_list(activities)
    retweets = retweet_analysis.evaluate()
    text.append(f'most retweeteted tweets are from {retweets[0][0]}, {retweets[1][0]} and {retweets[2][0]}')
    
    time_activity_analysis = ActivityAnalysis()
    time_activity_analysis.add_activity_list([ a for a in activities if not a.get_metadata()["retweet"] ])
    activity_times = time_activity_analysis.evaluate()
    activity_dow = dict()
    for dow in activity_times:
        activity_dow[dow] = 0.
        for h in range(24):
            activity_dow[dow] += activity_times[dow]["hours"][h]
    li_activity_dow = []
    for dow in activity_dow:
        li_activity_dow.append((dow, activity_dow[dow]))
    li_activity_dow.sort(key= lambda x : x[1], reverse=True)
    text.append(f'highest twitter activity at {li_activity_dow[0][0]} ({activity_times[li_activity_dow[0][0]]["activity"]:.2f}%), {li_activity_dow[1][0]} ({activity_times[li_activity_dow[1][0]]["activity"]:.2f}%) and {li_activity_dow[2][0]} ({activity_times[li_activity_dow[2][0]]["activity"]:.2f}%)')
    
    return "\n".join(text)


def main():
    if len(sys.argv) != 2:
        username = "@ReleasePreview"
    else:
        username = sys.argv[1]
    tweet = twitter(username)
    if not tweet is None:
        print(tweet)


if __name__ == "__main__":
    main()