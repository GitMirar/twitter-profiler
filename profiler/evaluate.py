import datetime
import gensim
import hdbscan
import numpy as np
from gensim.parsing.preprocessing import STOPWORDS
from gensim.corpora.dictionary import Dictionary
from collections import defaultdict

class EvaluationModule:

    def __init__(self):
        self.activities = []

    def add_activity(self, new_activity):
        """
        add activity to EvaluationModule
        """
        self.activities.append(new_activity)

    def add_activity_list(self, new_activity_list):
        """
        add activity list
        """
        [ self.activities.append(a) for a in new_activity_list ]

    def evaluate(self):
        """
        perform evaluation of added activities
        """
        pass


class ClusterByDate(EvaluationModule):

    MIN_CLUSTER_SIZE = 10

    def __init__(self):
        EvaluationModule.__init__(self)

    def evaluate(self):
        """
        cluster activities by time
        """

        times = [ a.get_date() for a in self.activities ]
        times = [ datetime.datetime.fromisoformat(d) for d in times if not d is None ]
        times_ts = [ d.timestamp() for d in times ]
        times_m = np.reshape(times_ts, (-1, 1))
        clusterer = hdbscan.HDBSCAN(min_cluster_size=self.MIN_CLUSTER_SIZE, metric="manhattan")
        clusterer.fit(times_m)
        clusters = []
        for cluster in range(clusterer.labels_.max()):
            clusters.append([])
            for i in range(len(clusterer.labels_)):
                if clusterer.labels_[i] == cluster:
                    clusters[cluster].append(self.activities[i])

        return clusters


class TopicAnalysis(EvaluationModule):

    MIN_WORD_SIZE = 4
    TOPIC_WORDS = 10

    def __init__(self):
        EvaluationModule.__init__(self)

    def evaluate(self):
        """
        perform LDA analysis on content fields of provided activities
        """
        # get text content from activities
        documents = [ a.get_content() for a in self.activities ]
        documents = [ d for d in documents if not d is [] ]
        urls = []
        [ [ urls.append(url) for url in a.get_urls() ] for a in self.activities ]
        # remove stopwords and urls
        texts = [ [word for word in document.lower().split() if word not in STOPWORDS 
            and word not in urls ] for document in documents ]
        texts = [ [ word for word in doc if not word[:4] == "http" ] for doc in texts ]
        # remove special characters
        text_nsc = []
        [ text_nsc.append([ "".join([ c for c in word if str.isalnum(c) ])
            for word in document ]) for document in texts ]
        text_nsc = [ [ word for word in documents if len(word) >= self.MIN_WORD_SIZE ] for documents in text_nsc ]
        frequency = defaultdict(int)
        for doc in text_nsc:
            for token in doc:
                frequency[token] += 1
        text_nsc = [ [token for token in doc if frequency[token] > 1 ] for doc in text_nsc ]
        dictionary = Dictionary(text_nsc)
        corpus = [ dictionary.doc2bow(doc) for doc in text_nsc ]
        model = gensim.models.LdaModel(corpus=corpus, num_topics=10, id2word=dictionary, passes=4, minimum_probability=0.9, random_state=1)
        result = []
        for topicno in range(model.num_topics):
            result.append(" ".join([ i[0] for i in model.show_topic(topicno)[:self.TOPIC_WORDS] ]))
        result_uniq = []
        [ result_uniq.append(r) for r in result if not r in result_uniq ]
        return result_uniq


class TimeClusteredTopics(EvaluationModule):

    def __init__(self):
        EvaluationModule.__init__(self)

    def evaluate(self):
        """
        time based topic clustering
        """
        # sort activities
        self.activities.sort(key = lambda x : datetime.datetime.fromisoformat(x.get_date()).timestamp(), reverse=True)
        cluster_by_date = ClusterByDate()
        cluster_by_date.add_activity_list(self.activities)
        clusters = cluster_by_date.evaluate()
        
        results = dict()

        for cluster in clusters:
            topic_analysis = TopicAnalysis()
            n = 0.
            dates = []
            for cluster_activity in cluster:
                topic_analysis.add_activity(cluster_activity)
                n += datetime.datetime.fromisoformat(cluster_activity.get_date()).timestamp()
                dates.append(cluster_activity.get_date())
            av_date = datetime.datetime.fromtimestamp(n/float(len(cluster))).isoformat()
            topics = topic_analysis.evaluate()
            results[av_date] = dict()
            results[av_date]["topics"] = topics
            results[av_date]["count"] = len(cluster)
            results[av_date]["dates"] = dates

        return results

    
class ActivityAnalysis(EvaluationModule):

    MAPPING_DOW = {  "Monday"    : 0,
                     "Tuesday"   : 1,
                     "Wednesday" : 2,
                     "Thursday"  : 3,
                     "Friday"    : 4,
                     "Saturday"  : 5,
                     "Sunday"    : 6}

    def __init__(self):
        """
        initialize ActivityAnalysis module
        """
        EvaluationModule.__init__(self)

    def evaluate(self):
        """
        evaluate the activity for each week of day and hourly slots
        """
        dates = [ datetime.datetime.fromisoformat(a.get_date()) for a in self.activities ]
        activity_summary = dict()
        activity_summary = dict()
        for d in self.MAPPING_DOW:
            activity_summary[d] = dict()
            activity_summary[d]["hours"] = [ 0 for i in range(24) ]
            activity_summary[d]["activity"] = 0
        # get distribution of activity through the week
        dow = dict()
        for d in range(7):
            dow[d] = 0
        for date in dates:
            dow[date.weekday()] += 1
        total_datapoints = len(dates)        
        for d in activity_summary:
            activity_summary[d]["activity"] = 100. / total_datapoints * dow[self.MAPPING_DOW[d]]
            # get activity for each hour based on dow
            day_activity = dict()
            for i in range(24):
                day_activity[i] = 0
            for datum in dates:
                if datum.weekday() == self.MAPPING_DOW[d]:
                    day_activity[datum.hour] += 1
            for a in day_activity:
                activity_summary[d]["hours"][a] = 100. / total_datapoints * day_activity[a]
        return activity_summary


class RetweetAnalysis(EvaluationModule):

    def __init__(self):
        EvaluationModule.__init__(self)

    def evaluate(self):
        retweets = dict()
        for tweet in self.activities:
            if tweet.get_metadata()["retweet"]:
                user = tweet.get_metadata()["username"]
                if not user in retweets:
                    retweets[user] = 1
                else:
                    retweets[user] += 1
        sorted_retweets = []
        for user in retweets:
            sorted_retweets.append((user, retweets[user]))
        sorted_retweets.sort(key= lambda x : x[1], reverse=True)
        return sorted_retweets