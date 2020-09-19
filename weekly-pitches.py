from pybaseball import statcast as sc
import tweepy
from configparser import ConfigParser
import datetime
from datetime import timedelta
import baseball_tweet


config = ConfigParser()
config.read("config.ini")
# AUTH
consumer_key = config["KEYS"]["consumer_key"]
consumer_secret = config["KEYS"]["consumer_secret"]
access_token = config["KEYS"]["access_token"]
access_token_secret = config["KEYS"]["access_token_secret"]
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

today = datetime.date.today()
date_min = today - timedelta(days=today.weekday()+7)
date_max = today - timedelta(days=today.isoweekday())
date_min, date_max = str(date_min), str(date_max)
data = sc(start_dt=date_min, end_dt=date_max)
general_cols = ["player_name", "game_date", "home_team", "away_team", "inning", "inning_topbot", "outs_when_up", "balls", "strikes", "pitch_number"]

# 3 fastest pitches
fastest_tweet = baseball_tweet.Baseball_tweet(api, "Last weeks #{0} fastest pitch by {1} with {2} MPH!", general_cols, date_min, date_max)
fastest_tweet.rank_data(data, "release_speed")
fastest_tweet.post_tweet()
# 3 most movement
movement_tweet = baseball_tweet.Movement_pitch(api, "Last weeks #{0} pitch with most movement by {1}, {2:.2f} inches of total movement!", general_cols, date_min, date_max)
movement_tweet.rank_data(data, "total_move")
movement_tweet.post_tweet()

# swing and miss farthest from zone, plate_x, plate_z
wiff_tweet = baseball_tweet.Wiff_pitch(api, "Last weeks #{0} greatest trickster by {1} with {2:.2f} ft to the zone!", general_cols, date_min, date_max)
wiff_tweet.rank_data(data, "zone_distance")
wiff_tweet.post_tweet()
