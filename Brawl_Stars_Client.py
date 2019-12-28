import numpy as np
import requests
import pandas as pd
import datetime
from dateutil import tz



class Game:
    def __init__(self, game_data):
        self.parse_game_data(game_data)
    def parse_game_data(self, game_data):
        self.time = game_data["battleTime"]
        self.mode = game_data["battle"]["mode"]
        self.map = game_data["event"]["map"]
        try:
            self.result = game_data["battle"]["result"]
        except:
            assert False, "This might be a single player mode, {}".format(game_data["battle"]["mode"])
        try:
            self.team1 = [Player(game_data["battle"]["teams"][0][0]),
                          Player(game_data["battle"]["teams"][0][1]),
                          Player(game_data["battle"]["teams"][0][2])]
            self.team2 = [Player(game_data["battle"]["teams"][1][0]),
                          Player(game_data["battle"]["teams"][1][1]),
                          Player(game_data["battle"]["teams"][1][2])]
        except:
            assert False, "This might be a single player mode, {}".format(game_data["battle"]["mode"])

class Player:
    def __init__(self, player_data):
        self.tag = player_data["tag"]
        self.name = player_data["name"]
        self.brawler = player_data["brawler"]["name"]
        try:
            self.trophies = player_data["brawler"]["trophies"]
        except:
#             print("could not acess trophies")
            self.trophies = None
        try:
            self.level = player_data["brawler"]["power"]
        except:
#             print("Could not access level")
            self.level = None
    
class BattleLog:
    def __init__(self, player_source, data):
        self.player_source = player_source
        self.games = self.parse_data(data)
        self.data = data
    def parse_data(self, data):
        games = []
        for game_data in data:
            if game_data["battle"]["mode"] not in {"duoShowdown", "soloShowdown", "takedown", "bigGame", "bossFight", "loneStar", "roboRumble"}:
                games.append(Game(game_data))
        return games
    def make_df(self):
        """
        The function to convert a battle log to a pandas DataFrame.
        """
        d = {"source":[],
            "time":[],
             "mode":[],
             "map":[],
             "result":[],
            }
        for team_num in [1,2]:
            for player_num in [1,2,3]:
                base = "team{}_player{}_".format(team_num, player_num)
                d[base + "tag"] = []
                d[base + "name"] = []
                d[base + "brawler"] = []
                d[base + "trophies"] = []
                d[base + "level"] = []
        for game in self.games:
            d["source"].append(self.player_source)
            d["time"].append(game.time)
            d["mode"].append(game.mode)
            d["map"].append(game.map)
            d["result"].append(game.result)
            for team_num in [1,2]:
                for player_num in [1,2,3]:
                    if team_num == 1:
                        team = game.team1
                    else:
                        team = game.team2
                    base = "team{}_player{}_".format(team_num, player_num)
                    d[base + "tag"].append(team[player_num - 1].tag)
                    d[base + "name"].append(team[player_num - 1].name)
                    d[base + "brawler"].append(team[player_num - 1].brawler)
                    d[base + "trophies"].append(team[player_num - 1].trophies)
                    d[base + "level"].append(team[player_num - 1].level)
        df = pd.DataFrame(d)
        return df

class Client:
    """
    A class that retreives the data from Brawl Stars Official API.
    
    Attributes:
        autorization_key (string): Key used to access data from server.
        base_url (string): The server where the data is stored.
        data (dict): Key is the url and the value is . This allows for memozied lookup for data that has been accessed recentely instead of sending an addition request to the server. 
    """
    def __init__(self):
        self.authorization_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjA5ZWQxNjJlLWE2OTktNGU0YS05MDk4LTdjNjM2MDJlMDQ0YiIsImlhdCI6MTU3NzIzODQ5Mywic3ViIjoiZGV2ZWxvcGVyLzQ4ZTFjNWRmLTU1ZTktYmYyYS01MGMxLWQ0NzE1ZDYwNjA5NiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMjU1LjI1NS4yNTUuMCIsIjY4LjEwMC4xMDEuMTQ5Il0sInR5cGUiOiJjbGllbnQifV19.x5iQjAxFNmgGtacmuPok1-C-s2BVVeHeHxHfF0LzhwZOT2ICNiQTCd4yTspj6vPLOP5h-IkOLPs27mIMoBlq3A"
        self.base_url = "https://api.brawlstars.com/v1"
        self.data = dict()
    def get_data(self, url, time = datetime.timedelta(minutes = 0)):
        """
        This function makes a request to brawl stars server. If the same request is made within the parameter time, this function will return the data in its data dictionary. 
        
        Parameters:
            url (string): The unique end part of the url to send to the server as specified in the Official Brawl Stars API documentation.
            time (datetime.timedelta): The time allowed before must contact the server again instead of doing a memomoized lookup.
        
        Returns:
            The json data received from the server or False if there was an error.
        """
        headers = {"authorization": "Bearer " + self.authorization_key}
        full_url = self.base_url + url
        if (full_url in self.data.keys()) and \
            (self.data[full_url]["time_accessed"] + time > datetime.datetime.now()):
            data = self.data[full_url]["data"]
        else:
            r = requests.get(url = full_url, headers = headers)
            data = r.json()
            self.data[full_url] = dict()
            if r.status_code != 200:
                if  url[:10] =="/players/%" and url[:12] != "/players/%23":
                    pass
                else:
                    print("Something went wrong.")
                    print(full_url)
                self.data[full_url]["data"] = False
                self.data[full_url]["time_accessed"] = datetime.datetime.now()
                return False
            else:
                self.data[full_url]["data"] = data
                self.data[full_url]["time_accessed"] = datetime.datetime.now()
        return data
    def get_player(self, player_id):
        """
        This function returns infromation about a player.
        
        Parameters:
            player_id (string): Unique hash tag in brawl stars.
        
        Returns:
            data (dict): Data has attributes from server.
        """
        data = self.get_data("/players/%" + player_id[1:])
        if data is False:
            data = self.get_data("/players/%23" + player_id[1:])
            if data is False:
                data = {'tag': None, 'name': None, 'nameColor': None, 'trophies': None, 'highestTrophies': None, 'highestPowerPlayPoints': None, 'expLevel': None, 'expPoints': None, 'isQualifiedFromChampionshipChallenge': None, '3vs3Victories': None, 'soloVictories': None, 'duoVictories': None, 'bestRoboRumbleTime': None, 'bestTimeAsBigBrawler': None, 'club': {'tag': None, 'name': None}, 'brawlers': []}
        return data
    def get_player_battle_log(self, player_id):
        full_data = self.get_data("/players/%" + player_id[1:] + "/battlelog")
        if full_data is False:
            full_data = self.get_data("/players/%23" + player_id[1:] + "/battlelog")
            if full_data is False:
                battle_log_data = {}
            else:
                battle_log_data = full_data["items"]
        else:
            battle_log_data = full_data["items"]
        return BattleLog(player_id, battle_log_data)
    def get_player_battle_logs_df(self, ids, mode = None, MAP = None, filter_type = None, filter_trophy_cutoff = 900):
        """
        This function returns a players battle log information in the form of a pandas Data Frame.
        
        Parameters:
            ids (list or string): List of unique hash tag in brawl stars.
            mode (string): Filters the df for the mode the game is played.
            MAP (string): Filters the df for the map where the game is played.
            filter_type (string): The filter_type can be 'Both Teams Greater Than trophy_cutoff' or 'One Team Greater Than trophy_cutoff'. The first option filters for games that have both teams matchamking above a certain trophy cutoff. The second option filters for games that have at least one team matchmaking above a certain trophy cutoff.
            filter_trophy_cutoff (string): When using the filter_type, this is the trophy cutoff used.
        Returns:
            Pandas Data Frame
        """
        def divide_and_conquer_combine(df_list):
            """
            Combines a list of dfs efficiently.
            """
            if len(df_list) < 1000:
                full = dfs[0]
                for i in range(1,len(df_list)):
                    full = full.append(dfs[i])
                return full
            else:
                mid_index = int(len(df_list)/2)
                left = divide_and_conquer_combine(df_list[:mid_index])
                right = divide_and_conquer_combine(df_list[mid_index:])
                full = left.append(right)
                print(full.shape)
                return full
        if type(ids) == str:
            ids = [ids]
        dfs = []
        for player in ids:
            battle_log = self.get_player_battle_log(player)
            dfs.append(battle_log.make_df())
        full = divide_and_conquer_combine(dfs)
        df = full
        
        if mode != None:
            df = df[df["mode"] == mode]
        if MAP != None:
            df = df[df["map"] == MAP]
        if filter_type == "Both Teams Greater Than trophy_cutoff":
            df = df[(df[["team1_player1_trophies","team1_player2_trophies", "team1_player3_trophies"]].max(axis = 1) > trophy_cutoff) & \
                (df[["team2_player1_trophies","team2_player2_trophies", "team2_player3_trophies"]].max(axis = 1) > trophy_cutoff)]
        elif filter_type == "One Team Greater Than trophy_cutoff":
            df = df[(df[["team1_player1_trophies","team1_player2_trophies", "team1_player3_trophies"]].max(axis = 1) > trophy_cutoff) | \
                (df[["team2_player1_trophies","team2_player2_trophies", "team2_player3_trophies"]].max(axis = 1) > trophy_cutoff)]
        df['hash'] = df["time"].apply(hash) + df["mode"].apply(hash) + df["map"].apply(hash)
        df['time'] = pd.to_datetime(df['time'], utc = True)
        to_zone = tz.tzlocal()
        df["time"] = df["time"].dt.tz_convert(to_zone)
        df = df.drop_duplicates("hash")
        return df

    
    def get_rankings(self, country_code = "global", limit = 200):
        """
        This function returns the top players who have the most trophies in some region.
        
        Parameters:
            country_code (string): region to search for rankings. Use global or 2 letter country code https://www.iban.com/country-codes.
            limit (int): Can't be higher than 200. The maximum number of players to return.
        
        Returns:
            dictionary of the data from brawl stats.
        """
        url = "/rankings/{}/players?limit={}".format(country_code, limit)
        return self.get_data(url)["items"]
    def get_brawler_rankings(self, brawler, country_code = "global", limit = 200):
        """
        This function returns the top players for a particular brawler in some region.
        
        Parameters:
            brawler (int or string): The brawlers id or name.
            country_code (string): region to search for rankings. Use global or 2 letter country code https://www.iban.com/country-codes.
            limit (int): Can't be higher than 200. The maximum number of players to return.
        
        Returns:
            dictionary of the data from brawl stats.
        """
        if type(brawler) == int:
            url = "/rankings/{}/brawlers/{}?limit={}".format(country_code, brawler,limit)
        elif type(brawler) == str:
            brawlers = {e["name"]:e["id"] for e in self.get_brawlers()}
            brawler_id = brawlers[brawler]
            url = "/rankings/{}/brawlers/{}?limit={}".format(country_code, brawler_id,limit)
        return self.get_data(url)["items"]
    def get_brawlers(self):
        """
        This function returns brawlers and some information about the brawler.

        Returns:
            dictionary of the data from brawl stats.
        """
        url = "/brawlers"
        return self.get_data(url)["items"]
    def get_player_ids(self, size):
        """
        This function returns a list of ids that varies in size depending on the parameter size.
        
        Parameters:
            size (string): Possible sizes is 'large', 'small', and 'test'. Large gets all players that are on major country leaderboards for brawlers and total trophies. Small gets all the players who are on the global leaderboard for total trophies. Test gets the top 20 players who are on the global leaderboard for total trophies.
        
        Returns:
            Dictionary of player_ids as keys with their names as values.
        """

        player_ids = dict()
        if size == "large":
            brawlers = {e["name"]:e["id"] for e in self.get_brawlers()}
            countries = ["global", "US", "CA", "KP","KR", "JP", "IN", "CH", "SE", "CN", "DK", "AU", "MX"]
            player_ids = dict()
            for country in countries:
                for brawler_id in brawlers.values():
                    for player in self.get_brawler_rankings(brawler_id, country):
                        player_ids[player["tag"]] = player["name"]
                for player in self.get_rankings(country):
                    player_ids[player["tag"]] = player["name"]
            return player_ids
        elif size == "small":
            player_ids = dict()
            for player in self.get_rankings():
                player_ids[player["tag"]] = player["name"]
            return player_ids
        elif size == "test":
            player_ids = dict()
            for player in self.get_rankings(limit = 20):
                player_ids[player["tag"]] = player["name"]
            return player_ids
        else:
            assert False, "Not a valid size."
    def get_test_df(self):
        """
        This is a function to quickly get some data to play around with.
        """
        ids = self.get_player_ids("test")
        df = get_player_battle_logs_df(ids)
        return df



