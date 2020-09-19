from pybaseball import playerid_lookup
from bs4 import BeautifulSoup
import requests
import shutil
from tweepy.binder import bind_api


def savant_clip(pitch, date_min, date_max):
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


def download_file(url):
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


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
