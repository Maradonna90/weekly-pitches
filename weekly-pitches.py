from pybaseball import statcast as sc
import math
from pybaseball import playerid_lookup
from bs4 import BeautifulSoup
import requests
import tweepy
from tweepy.binder import bind_api
import shutil
import time
from configparser import ConfigParser
import datetime
from datetime import timedelta
import os


def get_media_upload_status(api, *args, **kwargs):
    """ :reference: https://developer.twitter.com/en/docs/twitter-api/v1/media/upload-media/api-reference/get-media-upload-status
            :allowed_param:
        """
    "GET https://upload.twitter.com/1.1/media/upload.json?command=STATUS&media_id=710511363345354753"
    return bind_api(
            api=api,
            path='/media/upload.json',
            payload_type='media',
            allowed_param=['command', 'media_id'],
            upload_api=True,
            require_auth=True
    )(*args, **kwargs)


def download_file(url):
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


def distance_point_to_strikezone(inp):
    x, y = inp[0], inp[1]
    x_min = -1
    x_max = 1
    y_max = 3.5
    y_min = 1.5
    if x <= x_min:
        if y <= y_min:
            return math.sqrt((x_min-x)**2 + (y_min-y)**2)
        elif(y > y_max):
            return math.sqrt((x_min-x)**2 + (y_max-y)**2)
        elif((y >= y_min) & (y <= y_max)):
            return x_min - x
        else:
            if ((x > x_min) & (x < x_max)):
                if (y < y_min):
                    return y_min - y
                elif (y > y_max):
                    return y - y_max
            else:
                if (x > x_max):
                    if (y < y_min):
                        return math.sqrt((x_max-x)**2 + (y_min-y)**2)
                    elif(y > y_max):
                        return math.sqrt((x_max-x)**2 + (y_max-y)**2)
                    elif((y >= y_min) & (y <= y_max)):
                        return x - x_max
    return 0


def savant_clip(pitch):
    clip_url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfGT=R%7C&hfC=[count]%7C&hfSea=[season]%7C&hfSit=&player_type=pitcher&hfOuts=[outs]%7C&opponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=[date_min]&game_date_lt=[date_max]&hfInfield=&team=&position=&hfOutfield=&hfRO=&home_road=&hfFlag=&hfPull=&pitchers_lookup%5B%5D=[pitcher_id]&metric_1=api_p_release_speed&metric_1_gt=[min_speed]&metric_1_lt=[max_speed]&hfInn=[Inning]|&min_pitches=0&min_results=0&group_by=name&sort_col=pitches&player_event_sort=h_launch_speed&sort_order=desc&min_pas=0&type=details&player_id=[pitcher_id]"
    p_name = pitch['player_name'].split()
    p_id = playerid_lookup(p_name[1], p_name[0])['key_mlbam'].values
    # print(p_id)
    pitch_map = {
        "[Inning]": int(pitch['inning']),
        "[pitcher_id]": p_id[0],
        "[date_min]": date_min,
        "[date_max]": date_max,
        "[count]": str(int(pitch['balls']))+str(int(pitch['strikes'])),
        "[season]": "2020",
        "[outs]": int(pitch['outs_when_up']),
        "[min_speed]": int(pitch["release_speed"]-1),
        "[max_speed]": int(pitch["release_speed"]+1)
    }
    for k, v in pitch_map.items():
        clip_url = clip_url.replace(k, str(v))
    site = requests.get(clip_url)
    soup = BeautifulSoup(site.text, features="lxml")
    for link in soup.find_all('a'):
        clip_savant = requests.get("https://baseballsavant.mlb.com"+link.get('href'))
        clip_soup = BeautifulSoup(clip_savant.text, features='lxml')
        video_obj = clip_soup.find("video", id="sporty")
        clip_url = video_obj.find('source').get('src')
        return clip_url


def post_tweet(pitches, type, metric):
    text_type = {
        "fastest": {
            "text": "Last weeks #[rank] fastest pitch by [pitcher_name] with [release_speed]MPH!",
            "fields": {
                "[pitcher_name]": "player_name",
                "[release_speed]": "release_speed"
            }
        },
        "movement": {
            "text": "Last weeks #[rank] pitch with most movement by [pitcher_name], [total_move] inches of total movement!",
            "fields": {
                "[pitcher_name]": "player_name",
                "[total_move]": "total_move"
            }
        },
        "whiffer": {
            "text": "Last weeks #[rank] greatest trickster by [pitcher_name] with [zone_distance]ft to the zone!",
            "fields": {
                "[pitcher_name]": "player_name",
                "[zone_distance]": "zone_distance"
            }
        }
    }

    for i, (_, row) in enumerate(pitches.iterrows()):
        generic_text = text_type[type]["text"]
        for k, v in text_type[type]["fields"].items():
            generic_text = generic_text.replace("[rank]", str(i+1))
            generic_text = generic_text.replace(k, str(row[v]))
        tweet_text = generic_text
        # print(row['url'])
        video = download_file(row['url'])

        # Generate text tweet with media (video)
        media = api.media_upload(video)
        while get_media_upload_status(api, command="STATUS", media_id=media.media_id_string).processing_info["state"] != 'succeeded':
            time.sleep(1)
        media_ids = [media.media_id_string]
        print(media_ids)
        status = api.update_status(status=tweet_text, media_ids=media_ids)
        os.remove(video)


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
fastest = data.nlargest(3, columns=["release_speed"])
print("fastest\n", fastest.loc[:, ["release_speed"] + general_cols])
fastest['url'] = fastest.apply(savant_clip, axis=1)
post_tweet(fastest, "fastest", "release_speed")

# 3 most movement
data["total_move"] = data["pfx_z"].abs() + data["pfx_x"].abs()
move = data.nlargest(3, columns=["total_move"])
print("movement\n", move.loc[:, ["total_move"] + general_cols].to_string())
move['url'] = move.apply(savant_clip, axis=1)
post_tweet(move, "movement", "total_move")

# swing and miss farthest from zone, plate_x, plate_z
miss = data.loc[data['type'] == 'S']
distances = miss.loc[:, ["plate_x", "plate_z"]].apply(distance_point_to_strikezone, axis=1, raw=True)
miss.insert(0, "zone_distance", value=distances)
miss = miss.loc[miss['zone_distance'] > 0]
miss = miss.nlargest(3, columns=["zone_distance"])
print("miss & swings\n", miss.loc[:, ["zone_distance"] + general_cols])
miss['url'] = miss.apply(savant_clip, axis=1)
post_tweet(miss, "whiffer", "zone_distance")
