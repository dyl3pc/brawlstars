# Using Machine Learning to Predict Wins of Brawl Stars Games
## Intro
Brawl Stars is a mobile video game developed by Supercell (same developers of Clash Royale and Clash of Clans). I aimed to create a machine learning model that could predict the outcome of games given a set of features associated with the players in the game. I was particularly interested in the idea of finding a best team composition. I take a short detour on what appears to be a similar problem: best of rock paper scissors game. Overall, I gained experience collecting my own data using an asynchronous client, pandas for data cleaning, and training various machine learning algorithms using Scikit-learn and TensorFlow-Keras.

## Data Collection
#### `get_data.ipynb`
In 'client.py', I created an asynchronous client to collect game data from the Brawl Stars official API (developer.brawlstars.com). The Brawl Stars API only has a list of recently played matches by player. So starting from the top 200 players as a seed, I recursively added players to pool of player ids from which I subsequently fetched all of their recently played games. All the data was saved into an sqlite3 database which has approximately 4 million games and information on 350 thousand players.

## Data Cleaning
#### `clean_data.ipynb`
Within Brawl Stars, there are numerous game modes each with different rules. In addition, there are different maps for each mode. I did not expect models to generalize between the game modes or between maps, so I filtered the data for the most popular game mode and map, which was Brawl Ball played on Sunny Soccer. Subsequent filtering was done to only include high level games which were determined based on match making rating (MMR). Higher level games were chosen for ease of predictability (there is a higher chance of mismatch in MMR) and for more interesting results. I planned to try to answer questions like: how much skill is involved, what are the best characters in the game, etc. These kinds of questions need high level game play. After filtering, there were 30 thousand unique games.

### Features
Brawl ball is a 3 vs. 3 game mode where teams aim to push a ball past a goal line. Each record represented a unique game in the data frame. Each game had the features 'team{team_num}_player{player_num}_{feature_type}' where 'team_num", 'player_num', and 'feature_type' were taken from '[1,2]', '[1,2,3]', and '["brawler", "trophies", "power", "highestTotalTrophies", "totalTrophies", "exp", "highestPowerPlay", "3vs3Victories", "soloVictories", "duoVictories", "highestBrawlerTrophies"]' respectively. There was a column "result" which was 1 if team 1 won the game and 0 if team 1 lost the game. The "result" column is the column that the model tries to predict. In the section about manual predictions, I go about explaining some of the features I think are worth mentioning.

## Developing a baseline
### Manual Predictions
As the self proclaimed human expert, I randomly took 20 games and correctly predicted 80% of the outcomes (team 1 win or loss). My general strategy was to look at features that included trophies then to look at the brawler feature. Without getting into the details of why there are so many different trophy features, 'trophies' is a numerical feature determined by a player's previous wins and losses. People earn trophies after winning a game and lose trophies after losses. To make the game fair, the matchmaking system uses trophies as a player's MMR. Theoretically, it should be easy to predict games based off a player's trophies; however, due to the matchmaking system, trophies are generally even on both teams. If the trophies were not so close, I believe a machine learning algorithm could easily predict the outcome of games.

Due to the matchmaking system placing trophies so close, I used brawler team composition as the second largest predictor. The categorical variable, "brawler", determines the one of 31 brawlers in the game used by a particular player during a game. What is interesting is that some brawlers are designed to counter (meaning having an edge over) other brawlers. The heart of the problem is that some brawlers counter other brawlers, and there is no "best" brawler in the game. In a way, it is like asking in Rock Paper Scissors whether rock, paper, or scissors is the strongest choice. For example, brawler A might counter brawler B, brawler B counters brawler C, and brawler C counters brawler A. Another interesting relationship is synergies which happen when a team composition complements itself. For example, the brawler "Poco" works well with tanks. In top competitive play "Poco" with tanks is a formidable composition; however, the team composition with "Poco" and mid to long range brawlers struggles. Learning the subtleties of team composition interaction is a very difficult task.

My manual prediction was 80%. I have played the game since its release and thus have logged upwards of 14,000 games. I am only feeding my algorithm 30,000 games and given the fact that humans learn significantly more quickly than computers I expect 80% to be a high upper bound.

### Other Sources
#### League of Legends
League of Legends is a popular 5 vs 5 video game which displays some of the same ideas of “counters” as shown in the manual predictions section. The article achieved around a 60% accuracy. League of Legends is vastly more complex and the article only uses 1700 games. Along with numerous other reasons, I have confidence that 60% would be a lower bound for one of my models.

https://hackernoon.com/league-of-legends-predicting-wins-in-champion-select-with-machine-learning-6496523a7ea7

#### Sports
Sport games are vastly more complex than simple video game prediction. Doing a quick search I found that the best models have about a 60-70% accuracy.
https://www.sciencedirect.com/science/article/pii/S2210832717301485

### Base models
#### `project.ipynb`
When the categorical variables were dropped (no consideration of team composition), Logistic regression, linear support vector machine, and ensemble model worked best with 65-66% accuracy. When the categorical variables were included (one hot encoded), the same three models performed equally well with around 67-68% accuracy. Including the categorical variables certainly increased the accuracy; however, not as much as I had anticipated. There is certainly room to improve in developing a model that can better understand the categorical variables.

## Similar Problems: Best of Rock Paper Scissors 
#### `rock_paper_scissors.ipynb`
As mentioned earlier, I anticipate the brawler match ups to be highly predictive of the outcome of the game. The wheel of brawlers countering brawlers is similar to rock paper scissors in that there is no definitive best choice to make between rock, paper, and scissor. By trying to solve this problem, I hope to get an understanding of which model has a high chance of working properly on my problem. The exact details can be found in `rock_paper_scissors.ipynb`.

As a summary of the results, I found that support vector machines (SVMs) worked well; however, they were limited by their computational complexity. It would simply take too long to train some the SVMs on anything more than 100,000 instances of 96 features. Neural nets seemed to be the optimal model for the task because they were not limited by the size of the data set. Thus they seemed to be the optimal model for my project which I planned to artificially enlarge the number of instances by 72 giving me more than 1.5 million training instances. Because I was using one hot encoding, my data set had over 250 features.

## Training my final model
#### `project.ipynb`
