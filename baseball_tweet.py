import utils
import os
import time
from pybaseball import playerid_reverse_lookup


class Baseball_tweet:

    def __init__(self, api, tweet_string, general_cols, date_min, date_max, rank=3):
        self.date_min = date_min
        self.date_max = date_max
        self.rank = rank
        self.ranked_data = None
        self.tweet_string = tweet_string
        self.api = api
        self.general_cols = general_cols
        self.metric = None

    def rank_data(self, data, row):
        """ rank the data """
        self.metric = row
        metric_data = data
        metric_data = metric_data.nlargest(self.rank, columns=row)
        print(metric_data.loc[:, [row] + self.general_cols])
        metric_data['url'] = metric_data.apply(utils.savant_clip, axis=1, date_min=self.date_min, date_max=self.date_max)
        self.ranked_data = metric_data

    def post_tweet(self):
        """ post the tweet """
        for i, (_, row) in enumerate(self.ranked_data.iterrows()):
            tweet_text = self.tweet_string.format(i+1, row["player_name"].upper(), row[self.metric])
            video = utils.download_file(row['url'])

            # Generate text tweet with media (video)
            media = self.api.media_upload(video)
            while utils.get_media_upload_status(self.api, command="STATUS", media_id=media.media_id_string).processing_info["state"] != 'succeeded':
                time.sleep(1)
            media_ids = [media.media_id_string]
            print(media_ids)
            print(tweet_text)
            status = self.api.update_status(status=tweet_text, media_ids=media_ids)
            os.remove(video)

    def calc_metric(self):
        pass


class Movement_pitch(Baseball_tweet):
    def rank_data(self, data, row):
        """ rank the data """
        self.metric = row
        metric_data = data
        metric_data["total_move"] = metric_data["pfx_z"].abs() + metric_data["pfx_x"].abs()
        metric_data = metric_data.nlargest(self.rank, columns=row)
        print(metric_data.loc[:, [row] + self.general_cols])
        metric_data['url'] = metric_data.apply(utils.savant_clip, axis=1, date_min=self.date_min, date_max=self.date_max)
        self.ranked_data = metric_data


class Wiff_pitch(Baseball_tweet):
    def rank_data(self, data, row):
        """ rank the data """
        self.metric = row
        metric_data = data.loc[data['description'] == 'swinging_strike']
        distances = metric_data.loc[:, ["plate_x", "plate_z", "sz_top", "sz_bot"]].apply(utils.calc_zone_distance, axis=1, raw=True)
        metric_data.insert(0, "zone_distance", value=distances)
        metric_data = metric_data.loc[metric_data['zone_distance'] > 0]
        metric_data = metric_data.nlargest(self.rank, columns=row)
        print(metric_data.loc[:, [row] + self.general_cols])
        metric_data['url'] = metric_data.apply(utils.savant_clip, axis=1, date_min=self.date_min, date_max=self.date_max)
        self.ranked_data = metric_data


class Framed_pitch(Baseball_tweet):
    def rank_data(self, data, row):
        """ rank the data """
        self.metric = row
        metric_data = data.loc[data['description'] == 'called_strike']
        distances = metric_data.loc[:, ["plate_x", "plate_z", "sz_top", "sz_bot"]].apply(utils.calc_zone_distance, axis=1, raw=True)
        metric_data.insert(0, "zone_distance", value=distances)
        metric_data = metric_data.loc[metric_data['zone_distance'] > 0]
        metric_data = metric_data.nlargest(self.rank, columns=row)
        catchers = playerid_reverse_lookup(metric_data.loc[:, ['fielder_2']].values.flatten(), key_type='mlbam')
        catchers = catchers['name_first'] + " " + catchers['name_last']
        catchers = catchers.apply(str.title)
        print(metric_data.loc[:, [row] + self.general_cols])
        metric_data['url'] = metric_data.apply(utils.savant_clip, axis=1, date_min=self.date_min, date_max=self.date_max)
        metric_data["player_name"] = catchers.values
        self.ranked_data = metric_data
