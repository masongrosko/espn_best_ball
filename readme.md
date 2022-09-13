# ESPN Best Ball

## Goals

### Run an espn best ball league

* Using the espn fantasy football api to upload draft files.
* Using the espn fantasy football api to update roster order.
* Using the espn fantasy football api to stream required players.

## League details

* **Scoring format**:
  * PPR
  * Best ball
    * **What**: Best ball is a fantasy football format where the highest-scoring players are optimized to form the starting lineup.  
    If a player on the bench outscores a player in the starting slot for that position, take the points of the bench player.
    * **Why**: We will not be doing in season roster management, best ball allows the draft to shine more
  * Head to head match-ups will not matter for final rankings. It will be based on total points scored throughout the season
* **Roster**:
  * Starting lineup:
    * 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX
  * Bench
    * 1 QB, 3 RB, 3 WR, 1 TE
  * Max Roster Limit:
    * QB - 2
    * RB - 5
    * WR - 5
    * TE - 2
* **Draft rounds**: 12 Rounds
* **Draft order**: Draft order will be randomized
* **League size**:
  * Max of 16 (including Andrew)
    * If we exceed the number of players we will create any necessary extra leagues, with players distributed equally across the leagues
* **Pick-by-pick draft strategies**:
  * We will not be utilizing custom pick-by-pick strategies
  * The default setting for all rounds is always "Best Available". On this setting, the system will draft the highest remaining player from any position that would not exceed the roster cap.
* **In season roster changes**: No roster changes throughout the season, except as stated below
  * Players will be "streamed" if there are not enough to populate the starting lineup
    * This will likely be due to injuries or BYE weeks
    * Players dropped in this way will be re-picked up the following week, no other team may pick them up
  * Season ending injuries will be "streamed"
* **Trades**: No trades are allowed
* **No live draft**: The draft csv file will be used to create a draft board for auto-draft
* **Post Draft**:
  * We will have a retrospective, draft analysis with all teams 1 week after
  * The teams will run automatically the whole season
    * If there is interest, we can duplicate the draft in a separate league and try some in season team management in that league.

## Glossary

*Streamed*
: Streaming a player means picking up the best available player at that position each week then dropping them the following week in favor of the new best available.
: For this league, weekly best available according to ESPN will be taken.
