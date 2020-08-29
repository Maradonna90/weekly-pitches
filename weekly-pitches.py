from pybaseball import statcast as sc
import math
import pandas as pd


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


data = sc(start_dt='2020-08-17', end_dt='2020-08-24')
general_cols = ["player_name", "game_date", "home_team", "away_team", "inning", "inning_topbot", "outs_when_up", "balls", "strikes", "pitch_number"]

# 3 fastest pitches
fastest = data.nlargest(3, columns=["release_speed"])
print("fastest\n", fastest.loc[:, ["release_speed"] + general_cols])

# 3 most movement
data["total_move"] = data["pfx_z"].abs() + data["pfx_x"].abs()
move = data.nlargest(3, columns=["total_move"])
print("movement\n", move.loc[:, ["total_move"] + general_cols].to_string())

# swing and miss farthest from zone, plate_x, plate_z
# type = "S"
miss = data.loc[data['type'] == 'S']
distances = miss.loc[:, ["plate_x", "plate_z"]].apply(distance_point_to_strikezone, axis=1, raw=True)
miss.insert(0, "zone_distance", value=distances)
miss = miss.loc[miss['zone_distance'] > 0]
miss = miss.nlargest(3, columns=["zone_distance"])
print("miss & swings\n", miss.loc[:, ["zone_distance"] + general_cols])

# https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfGT=R%7C&hfC=02%7C&hfSea=2020%7C&hfSit=&player_type=pitcher&hfOuts=1%7C&opponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=2020-08-20&game_date_lt=2020-08-20&hfInfield=&team=&position=&hfOutfield=&hfRO=&home_road=&hfFlag=&hfPull=&pitchers_lookup%5B%5D=425794&metric_1=&hfInn=7%7C&min_pitches=0&min_results=0&group_by=name&sort_col=pitches&player_event_sort=h_launch_speed&sort_order=desc&min_pas=0#results
