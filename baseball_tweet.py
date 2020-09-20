import utils
import os
import time
import math


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
            tweet_text = self.tweet_string.format(i+1, row["player_name"], row[self.metric])
            video = utils.download_file(row['url'])

            # Generate text tweet with media (video)
            media = self.api.media_upload(video)
            while utils.get_media_upload_status(self.api, command="STATUS", media_id=media.media_id_string).processing_info["state"] != 'succeeded':
                time.sleep(1)
            media_ids = [media.media_id_string]
            print(media_ids)
            print(tweet_text)
            # status = self.api.update_status(status=tweet_text, media_ids=media_ids)
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
        metric_data = data.loc[data['type'] == 'S']
        distances = metric_data.loc[:, ["plate_x", "plate_z"]].apply(self.calc_metric, axis=1, raw=True)
        metric_data.insert(0, "zone_distance", value=distances)
        metric_data = metric_data.loc[metric_data['zone_distance'] > 0]
        metric_data = metric_data.nlargest(self.rank, columns=row)
        print(metric_data.loc[:, [row] + self.general_cols])
        metric_data['url'] = metric_data.apply(utils.savant_clip, axis=1, date_min=self.date_min, date_max=self.date_max)
        self.ranked_data = metric_data

    def calc_metric(self, inp):
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
