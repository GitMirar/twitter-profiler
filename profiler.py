#!/usr/bin/env python3

import os
import datetime
import sys

from profiler.twitter import TwitterProfiler as TwitterProfiler
from profiler.evaluate import TopicAnalysis, ClusterByDate, TimeClusteredTopics, ActivityAnalysis, RetweetAnalysis

def overall_topics(activities):
    topics_analysis = TopicAnalysis()
    topics_analysis.add_activity_list(activities)
    topics = topics_analysis.evaluate()
    print ("### TOPIC ANALYSIS ###")
    for topic in topics[:3]:
        print(topic)
    print()
    print()
    print()


def clustered_topics(activities):
    tc_topics = TimeClusteredTopics()
    tc_topics.add_activity_list(activities)
    clusters = tc_topics.evaluate()
    print ("### CLUSTERED TOPIC ANALYSIS ###")
    keys = [ d for d in clusters ]
    keys.sort(key= lambda x : datetime.datetime.fromisoformat(x).timestamp(), reverse=True)
    for d in keys:
        print("== %s | %d ==" % (d, clusters[d]["count"]))
        for topic in clusters[d]["topics"][:1]:
            print(topic)
    print()
    print()
    print()
    

def activity_analysis(activities):
    act_analysis = ActivityAnalysis()
    act_analysis.add_activity_list(activities)
    timed_activities = act_analysis.evaluate()
    print ("### ACTIVITY TIME ANALYSIS ###")
    for dow in timed_activities:
        print("=== %s | %f ===" % (dow, timed_activities[dow]["activity"]))
        h = 0
        for hour in timed_activities[dow]["hours"]:
            print("%02d\t%f" % (h, hour))
            h += 1
    print()
    print()
    print()
    

def retweets(activities):
    retweet_analysis = RetweetAnalysis()
    retweet_analysis.add_activity_list(activities)
    retweets = retweet_analysis.evaluate()
    print ("### RETWEET ANALYSIS ###")
    for user in retweets[:5]:
        print("%d\t%s" % (user[1], user[0]))
    print()
    print()
    print()


def main():
    t = TwitterProfiler()
    if len(sys.argv) != 2:
        activities_cached = t.query_cached("@ReleasePreview")
    else:
        activities_cached = t.query_cached(sys.argv[1])

    if activities_cached is None or len(activities_cached) == 0:
        print("error fetching activities")
        return

    overall_topics(activities_cached)
    clustered_topics(activities_cached)
    activity_analysis([ a for a in activities_cached if not a.get_metadata()["retweet"] ])
    retweets(activities_cached)


if __name__ == "__main__":
    main()