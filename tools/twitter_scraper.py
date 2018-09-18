from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import datetime
import json


def get_url(url, headers, parameters=None):
    try:
        with closing(get(url, stream=True, headers=headers, params=parameters)) as resp:
            if resp.status_code == 200:
                return resp.content
            else:
                return None

    except RequestException as e:
        return None


def get_tweets_li(html):
    li_items = []
    for li in html.select("li"):
        if "stream-item" in li["class"]:
            li_items.append(li)
    return li_items


def parse_tweet(li_tweet):
    tweet = dict()
    for div in li_tweet.select("div"):
        if "class" in div.attrs and "tweet" in div["class"] and "data-tweet-id" in div.attrs:
            tweet["tweetId"] = div["data-tweet-id"]
            break
    context_div = None
    for div in li_tweet.select("div"):
        if "class" in div.attrs and "context" in div["class"]:
            context_div = div
            break
    if context_div is None:
        return None
    tweet["retweet"] = False
    for span in context_div.select("span"):
        if "class" in span.attrs and "Icon--retweeted" in span["class"]:
            tweet["retweet"] = True
            break
    content_div = None
    for div in li_tweet.select("div"):
        if "content" in div["class"]:
            content_div = div
            break
    if content_div is None:
        return None
    for span in content_div.select("span"):
        if "class" in span.attrs and "username" in span["class"]:
            tweet["username"] = "@%s" % span.select_one("b").contents[0]
            break
    for strong in content_div.select("strong"):
        if "class" in strong.attrs and "fullname" in strong["class"]:
            tweet["fullname"] = str(strong.contents[0])
            break
    for span in content_div.select("span"):
        if "class" in span.attrs and "_timestamp" in span["class"] and "data-time" in span.attrs:
            tweet["date"] = datetime.datetime.fromtimestamp(int(span["data-time"])).isoformat()
            break
    text_div = None
    for div in content_div.select("div"):
        if "class" in div.attrs and "js-tweet-text-container" in div["class"]:
            text_div = div
            break
    if text_div is None:
        return None
    tweet["hashtags"] = []
    tweet["links"] = []
    for a in text_div.select("a"):
        if "class" in a.attrs and "twitter-hashtag" in a["class"]:
            tweet["hashtags"].append("#%s" % a.select_one("b").contents[0])
        if "class" in a.attrs and "twitter-timeline-link" in a["class"] and "data-expanded-url" in a.attrs:
            tweet["links"].append(a["data-expanded-url"])
    for p in text_div.select("p"):
        if "class" in p.attrs and "TweetTextSize" in p["class"]:
            text = []
            for content in p.contents:
                if content.name is None:
                    text.append(str(content))
                elif content.name == "a":
                    a = content
                    if "class" in a.attrs and "twitter-hashtag" in a["class"]:
                        text.append("#%s" % a.select_one("b").contents[0])
                    elif "data-expanded-url" in a.attrs:
                        text.append(a["data-expanded-url"])
            tweet["text"] = "".join(text)
            break
    return tweet


def get_parse_tweets(url, headers, last_tweet=None):
    html_data = None
    if last_tweet is None:
        html_data = get_url(url, headers)
    else:
        p = { "max_position" : last_tweet }
        html_data = get_url(url, headers, parameters=p)
    if html_data is None:
        return None
    j_html = json.loads(html_data)
    html = BeautifulSoup(j_html["items_html"], 'html.parser')
    li_tweets = get_tweets_li(html)
    tweets = []
    for li_tweet in li_tweets:
        tweet = parse_tweet(li_tweet)
        if tweet is None:
            continue
        tweets.append(tweet)
    return tweets


def get_tweets(user, n=500):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'https://twitter.com/{user}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
        'X-Twitter-Active-User': 'yes',
        'X-Requested-With': 'XMLHttpRequest'
    }
    url = f'https://twitter.com/i/profiles/show/{user}/timeline/tweets?include_available_features=1&include_entities=1&include_new_items_bar=true'
    tweets = []
    last_tweet = None
    while len(tweets) < n:
        if not last_tweet is None:
            fetched_tweets = get_parse_tweets(url, headers, last_tweet)
        else:
            fetched_tweets = get_parse_tweets(url, headers)
        if fetched_tweets is None or len(fetched_tweets) == 0:
            # we assume no more tweets are available
            break
        last_tweet = fetched_tweets[-1]["tweetId"]
        [ tweets.append(t) for t in fetched_tweets ]
    return tweets