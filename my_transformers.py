from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import datetime
import numpy as np
from dateutil import tz
import math
import itertools
from sklearn.preprocessing import OneHotEncoder


class SpecialImputer(BaseEstimator, TransformerMixin):
    # this imputer replaces na values with the mean or median of a particular feature of the other players in the game
    def __init__(self, statistic = "mean"):
        self.statistic = statistic
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        X = X.copy()
        features = set()
        for column in X.columns:
            features.add(column[14:])
        features = list(features)
        for i in range(len(X)):
            for feature in features:
                values = []
                for team_num in [1,2]:
                    for player_num in [1,2,3]:
                        f = "team{}_player{}_{}".format(team_num, player_num, feature)
                        value = X.iat[i, X.columns.get_loc(f)]
                        if not math.isnan(value):
                            values.append(value)
                if len(values) != 0:
                    if self.statistic == "mean":
                        imputed_value = np.mean(values)
                    elif self.statistic == "median":
                        imputed_value = np.median(values)
                    else:
                        assert False, "not a valid statistic" + self.statistic
                else:
                    imputed_value = np.nan
                for team_num in [1,2]:
                    for player_num in [1,2,3]:
                        f = "team{}_player{}_{}".format(team_num, player_num, feature)
                        value = X.iat[i, X.columns.get_loc(f)]
                        if math.isnan(value):
                            X.iat[i, X.columns.get_loc(f)] = imputed_value
        return X

class ColumnSelector(BaseEstimator, TransformerMixin):
    # selects certain columns that seem to be of use
    def __init__(self):
        pass
    def fit(self, X, y = None):
        return self
    def transform(self, X, y = None):
        features_to_keep = ["trophies", "power", "highestTotalTrophies", "totalTrophies", "highestPowerPlay", "highestBrawlerTrophies", "brawler"]
        new_X = pd.DataFrame()
        for team_num in [1,2]:
            for player_num in [1,2,3]:
                for feature in features_to_keep:
                    f = "team{}_player{}_{}".format(team_num, player_num, feature)
                    new_X[f] = X[f]
        return new_X

class DropCategoricalColumns(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass
    def fit(self, X, y = None):
        return self
    def transform(self, X, y = None):
        X = X.copy()
        for team_num in [1,2]:
            for player_num in [1,2,3]:
                value = "team{}_player{}_brawler".format(team_num, player_num)
                X.drop(value, axis = 1, inplace = True)
        return X

class MyOneHotEncoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass
    def fit(self, X, y = None):
        return self
    def transform(self, X, y = None):
        brawlers = ['BIBI', 'TICK', 'SHELLY', '8-BIT', 'BARLEY', 'PAM', 'BEA', 'COLT', 'MORTIS', 'NITA', 'BULL', 'SPIKE', 'MAX', 'POCO', 'PENNY', 'LEON', 'JESSIE', 'EMZ',
                    'EL PRIMO', 'ROSA', 'CARL', 'BROCK', 'BO', 'GENE', 'DARRYL', 'PIPER', 'TARA', 'SANDY', 'DYNAMIKE', 'FRANK', 'CROW', 'RICO']
        for team_num in [1,2]:
            for player_num in [1,2,3]:
                f = "team{}_player{}_brawler".format(team_num, player_num)
                c = X[f]
                X[f] = pd.Categorical(X[f], categories=brawlers)
                X = pd.concat((X, pd.get_dummies(X[f])), axis = 1)
        return X


class DataImputer(BaseEstimator, TransformerMixin):
    # expands the dataset by switching the order of the teams which is arbitrary. Each team has 3! = 6 permutations. The data is also expanded so that team1 is switched with team2 whcih is also arbitrary. In total this imputer expands the data set by 6 * 6  * 2 = 72. The first 6 is from the permutations of the first team, the second 6 from the permutations of the second team, the 2 is from whether team1 is first or team2 is first.
    def __init__(self):
        pass
    def fit(self, X, y = None):
        return self
    def transform(self, X, y = None):
        features = set()
        for column in X.columns:
            features.add(column[14:])
        features = list(features)
        all_Xs = []
        first_team = list(itertools.permutations([1,2,3]))
        second_team = list(itertools.permutations([1,2,3]))
        for i1 in range(len(first_team)):
            for i2 in range(len(second_team)):
                new_X = X.copy()
                new_columns = dict()
                for player_num in [1,2,3]:
                    new_columns.update({"team{}_player{}_{}".format(1, player_num, feature):"team{}_player{}_{}".format(1, first_team[i1][player_num-1], feature) for feature in features})
                    new_columns.update({"team{}_player{}_{}".format(2, player_num, feature):"team{}_player{}_{}".format(2, second_team[i2][player_num-1], feature) for feature in features})
                all_Xs.append(new_X.rename(columns = new_columns))
                new_X = X.copy()
                for player_num in [1,2,3]:
                    new_columns.update({"team{}_player{}_{}".format(2, player_num, feature):"team{}_player{}_{}".format(1, first_team[i1][player_num-1], feature) for feature in features})
                    new_columns.update({"team{}_player{}_{}".format(1, player_num, feature):"team{}_player{}_{}".format(2, second_team[i2][player_num-1], feature) for feature in features})
                new_X["result"] = (new_X["result"] + 1) % 2
                all_Xs.append(new_X.rename(columns = new_columns))
        X = pd.concat(all_Xs)
        y = X["result"]
        X.drop("result", axis = 1, inplace = True)
        return X, y
