import aiohttp
import asyncio
import pandas as pd
import sqlite3
import datetime
import random
from dateutil import tz
import os


class Client():
    def __init__(self, database = "databases/test.db"):
        # self.authorization_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkaXNjb3JkX3VzZXJfaWQiOiI0NTU1MDQyNTQxMjQxNjMwNzMiLCJyZWFzb24iOiJTYXZlX01hdGNodXBfU3RhdGlzdGljcyIsInZlcnNpb24iOjEsImlhdCI6MTU2NDkyMDc4NH0.irTbacoWi1vW4DTsHUDgeIf3jPdUZA_85ev4tPDUo-g"
        self.authorization_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjZkNjFlNjcyLWIyYWItNDIwYy05OGZlLTI1NjljOGQ1OGQ3YyIsImlhdCI6MTU3Nzg2NjMwNiwic3ViIjoiZGV2ZWxvcGVyLzQ4ZTFjNWRmLTU1ZTktYmYyYS01MGMxLWQ0NzE1ZDYwNjA5NiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiNjguMTAwLjEwMS4xNDkiXSwidHlwZSI6ImNsaWVudCJ9XX0.XsR3hGwqwV6MLEiCBWTXe7sn0NV5TCQJcRl-9o7feAd7TG772Eqal7VGK4_C9vfn_RiGdy4q_VfIpxKFY2Jsdw"
        self.base_url = "https://api.brawlstars.com/v1"
        try:
            if database == "databases/test.db" and os.path.exists(database): os.remove(database)
        except:
            pass
        self.database = database
        self.throttle_rate = 0.15 # sec/token
        self.time_since_last_token = datetime.datetime.now(tz.tzlocal())
        self.conn = sqlite3.connect(self.database)
    async def get_token(self):
        if self.time_since_last_token + datetime.timedelta(seconds = self.throttle_rate) <= datetime.datetime.now(tz.tzlocal()):
            self.time_since_last_token = datetime.datetime.now(tz.tzlocal())
            return
        else:
            self.time_since_last_token += datetime.timedelta(seconds = self.throttle_rate)
            delta_time =  self.time_since_last_token - datetime.datetime.now(tz.tzlocal())
            # print("Waiting for {} seconds".format(int(delta_time.total_seconds())))
            return await asyncio.sleep(int(delta_time.total_seconds()))
    async def fetch(self, session, url):
        full_url = self.base_url + url
        # print(full_url)
        headers = {"authorization": "Bearer " + self.authorization_key}
        status = 429
        await self.get_token()
        # print(datetime.datetime.now())
        while status == 429:
            async with session.get(full_url, headers = headers) as r:
                data, status = await r.json(), r.status
            if status == 429:
                print("Throttle rate increased to {}".format(self.throttle_rate))
                await self.get_token()
        return data, status
    async def get_player(self, player_tag, add_to_database = False):
        tag = player_tag[1:]
        url = "/players/{}".format("%23" + tag)
        async with aiohttp.ClientSession() as session:
            data, status = await self.fetch(session, url)
        if status != 200:
            url = "/players/{}".format("%" + tag)
            async with aiohttp.ClientSession() as session:
                data, status = await self.fetch(session, url)
            if status != 200:
                assert False, "Status was not 200 {}, {}".format(data, status)
        if add_to_database == True:
            clean_dict = {"name":[], "highestTrophies":[]}
            for brawler in data["brawlers"]:
                clean_dict["name"].append(brawler["name"])
                clean_dict["highestTrophies"].append(brawler["highestTrophies"])
            df = pd.DataFrame(clean_dict)
            df["time_accessed"] = datetime.datetime.now(tz.tzlocal())
            df["player_id"] = player_tag
            df.to_sql(name = "brawler_highest_trophies", con = self.conn, if_exists = "append", index = False)
            del data["club"]
            del data["brawlers"]
            data["tag"] = "#" + data["tag"][1:]
            s = pd.Series(data)
            if "powerPlayPoints" not in s.index:
                s["powerPlayPoints"] = None
            s["time_accessed"] = datetime.datetime.now(tz.tzlocal())
            df = pd.DataFrame(s)
            df = df.transpose()
            df.to_sql(name = "players", con = self.conn, if_exists = "append", index = False)
        return data
    async def get_player_battle_log(self, player_tag, add_to_database = False):
        tag = player_tag[1:]
        url = "/players/{}/battlelog".format("%23" + tag)
        async with aiohttp.ClientSession() as session:
            data, status = await self.fetch(session, url)
        if status != 200:
            url = "/players/{}/battlelog".format("%" + tag)
            async with aiohttp.ClientSession() as session:
                data, status = await self.fetch(session, url)
            if status != 200:
                assert False, "Status was not 200 {}, {}".format(data, status)
        copy_data = data.copy()
        if add_to_database == True:
            clean_dict = dict()
            keys = ["time", "mode", "map", "type", "result", "duration"]
            for team_num in [1,2]:
                for player_num in [1,2,3]:
                    base = "team{}_player{}_".format(team_num, player_num)
                    keys.append(base + "tag")
                    keys.append(base + "brawler")
                    keys.append(base + "trophies")
                    keys.append(base + "power")
            for key in keys:
                clean_dict[key] = []
            for battle in data["items"]:
                if battle["battle"]["mode"] not in {"duoShowdown", "soloShowdown", "takedown", "bigGame", "bossFight", "loneStar", "roboRumble"}:
                    clean_dict["time"].append(battle["battleTime"])
                    clean_dict["mode"].append(battle["event"]["mode"])
                    clean_dict["map"].append(battle["event"]["map"])
                    clean_dict["type"].append(battle["battle"]["type"])
                    clean_dict["result"].append(battle["battle"]["result"])
                    clean_dict["duration"].append(battle["battle"]["duration"])
                    for team_num in [1,2]:
                        for player_num in [1,2,3]:
                            base = "team{}_player{}_".format(team_num, player_num)
                            clean_dict[base + "tag"].append(battle["battle"]["teams"][team_num - 1][player_num - 1]["tag"])
                            clean_dict[base + "brawler"].append(battle["battle"]["teams"][team_num - 1][player_num - 1]["brawler"]["name"])
                            if "trophies" in battle["battle"]["teams"][team_num - 1][player_num - 1]["brawler"].keys():
                                clean_dict[base + "trophies"].append(battle["battle"]["teams"][team_num - 1][player_num - 1]["brawler"]["trophies"])
                            else:
                                clean_dict[base + "trophies"].append(None)
                            if "power" in battle["battle"]["teams"][team_num - 1][player_num - 1]["brawler"].keys():
                                clean_dict[base + "power"].append(battle["battle"]["teams"][team_num - 1][player_num - 1]["brawler"]["power"])
                            else:
                                clean_dict[base + "power"].append(None)
            df = pd.DataFrame(clean_dict)
            df["source"] = player_tag
            df['time'] = pd.to_datetime(df['time'], utc = True)
            to_zone = tz.tzlocal()
            df["time"] = df["time"].dt.tz_convert(to_zone)
            df.to_sql(name = "battle_logs", con = self.conn, if_exists = "append", index = False)
        return data
    async def get_rankings(self, countryCode = "global", brawler_id = None, limit = 200):
        if brawler_id == None:
            url = "/rankings/{}/players?limit={}".format(countryCode, limit)
        else:
            url = "/rankings/{}/brawlers/{}?limit={}".format(countryCode, brawler_id, limit)
        async with aiohttp.ClientSession() as session:
            data, status = await self.fetch(session, url)
        if status != 200:
            assert False, "Status code was not 200 {}, {}".format(status, data)
        ids = dict()
        for player in data["items"]:
            ids[player["tag"]] = player["name"]
        return ids
    async def get_brawlers(self, add_to_database = False):
        url = "/brawlers"
        async with aiohttp.ClientSession() as session:
            data, status = await self.fetch(session, url)
        if status != 200:
            assert False, "Status code was not 200 {}, {}".format(status, data)
        if add_to_database:
            clean_dict = dict()
            clean_dict["id"] = []
            clean_dict["name"] = []
            for e in data["items"]:
                clean_dict["id"].append(e["id"])
                clean_dict["name"].append(e["name"])
            df = pd.DataFrame(clean_dict)
            df.to_sql(name = "brawlers", con = self.conn, if_exists = "replace", index = False)
        d = {brawler["id"]:brawler["name"] for brawler in data["items"]}
        return d
    async def get_ids(self, size):
        if size == "test":
            return await self.get_rankings(limit = 20)
        elif size == "small":
            return await self.get_rankings()
        elif size == "medium":
            brawlers = await self.get_brawlers(add_to_database = False)
            async def add_ids_to_dictionary(f, d, *args):
                ids = await f(*args)
                for key in ids:
                    d[key] = ids[key]
            d = dict()
            jobs = [add_ids_to_dictionary(self.get_rankings, d, "global", brawler_id) for brawler_id in brawlers]
            jobs.append(add_ids_to_dictionary(self.get_rankings, d, "global"))
            loop = asyncio.get_event_loop()
            await asyncio.wait(jobs)
            return d
    async def add_battle_logs_to_database(self, ids):
        print("We will add {} player's battlelogs into database.".format(len(ids)))
        print("This should take approximately: {} hours as lower bound".format(len(ids)*self.throttle_rate/3600))
        ids = list(ids)
        start_time = datetime.datetime.now()
        i = 0
        jobs = []
        while i < len(ids):
            jobs.append(self.get_player_battle_log(ids[i], add_to_database = True))
            i += 1
            if i% 1000 == 0:
                await asyncio.wait(jobs)
                jobs = []
        await asyncio.wait(jobs)
        end_time = datetime.datetime.now()
        print("Time to complete run: {}".format(end_time - start_time))
    async def add_player_data_to_databases(self, ids):
        print("We will add {} player's battlelogs into database.".format(len(ids)))
        print("This should take approximately: {} hours as lower bound".format(len(ids)*self.throttle_rate/3600))
        ids = list(ids)
        start_time = datetime.datetime.now()
        i = 0
        jobs = []
        while i < len(ids):
            jobs.append(self.get_player(ids[i], add_to_database = True))
            i += 1
            if i% 1000 == 0:
                await asyncio.wait(jobs)
                jobs = []
        await asyncio.wait(jobs)
        end_time = datetime.datetime.now()
        print("Time to complete run: {}".format(end_time - start_time))
