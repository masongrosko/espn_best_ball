"""Rough best ball score."""

from dataclasses import dataclass
from typing import List

import pandas as pd
from espn_api.football import BoxPlayer, League


@dataclass
class IdealLineup:
    """Ideal best ball lineup."""

    qb: BoxPlayer
    wr1: BoxPlayer
    wr2: BoxPlayer
    rb1: BoxPlayer
    rb2: BoxPlayer
    te: BoxPlayer
    flex: BoxPlayer

    def total_points(self):
        """Sum up all the points."""
        return (
            self.qb.points
            + self.wr1.points
            + self.wr2.points
            + self.rb1.points
            + self.rb2.points
            + self.te.points
            + self.flex.points
        )


def player_with_max_points(list_of_players: List[BoxPlayer]) -> BoxPlayer:
    """Find player with max points in a list."""
    return list_of_players.pop(
        list_of_players.index(max(list_of_players, key=lambda x: x.points))
    )


def create_ideal_lineup(lineup: List[BoxPlayer]) -> IdealLineup:
    """Create an ideal lineup."""
    qbs = []
    rbs = []
    wrs = []
    tes = []
    for player in lineup:
        if "QB" in player.eligibleSlots:
            qbs.append(player)
        elif "RB" in player.eligibleSlots:
            rbs.append(player)
        elif "WR" in player.eligibleSlots:
            wrs.append(player)
        elif "TE" in player.eligibleSlots:
            tes.append(player)
        else:
            print(player, "does not match any eligible roles")

    return IdealLineup(
        qb=player_with_max_points(qbs),
        wr1=player_with_max_points(wrs),
        wr2=player_with_max_points(wrs),
        rb1=player_with_max_points(rbs),
        rb2=player_with_max_points(rbs),
        te=player_with_max_points(tes),
        flex=player_with_max_points(rbs + wrs + tes),
    )


def get_best_ball_scores(league: League) -> pd.DataFrame:
    """Get best ball scores for weeks so far."""
    out = {}
    for week in range(1, league.current_week):
        box_scores = league.box_scores(week)
        out[f"Week {week}"] = {}
        for box_score in box_scores:
            if box_score.home_team != 0:
                home_lineup = create_ideal_lineup(box_score.home_lineup)
                out[f"Week {week}"][
                    box_score.home_team.team_name
                ] = home_lineup.total_points()

            if box_score.away_team != 0:
                away_lineup = create_ideal_lineup(box_score.away_lineup)
                out[f"Week {week}"][
                    box_score.away_team.team_name  # type: ignore
                ] = away_lineup.total_points()

    return pd.DataFrame(out)


def main():
    """Run main function."""
    league = League(league_id=1030704919, year=2022)
    get_best_ball_scores(league).to_csv("hackathon_points.csv")


if __name__ == "__main__":
    main()
