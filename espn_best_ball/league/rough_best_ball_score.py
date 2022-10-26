"""Rough best ball score."""

from dataclasses import dataclass, field, fields
from typing import List

import pandas as pd
from espn_api.football import BoxPlayer, League, Team


@dataclass
class IdealLineup:
    """Ideal best ball lineup."""

    qb: BoxPlayer = field(metadata={"position": "QB"})
    wr1: BoxPlayer = field(metadata={"position": "WR"})
    wr2: BoxPlayer = field(metadata={"position": "WR"})
    rb1: BoxPlayer = field(metadata={"position": "RB"})
    rb2: BoxPlayer = field(metadata={"position": "RB"})
    te: BoxPlayer = field(metadata={"position": "TE"})
    flex: BoxPlayer = field(metadata={"position": "RB/WR/TE"})

    def total_points(self):
        """Sum up all the points."""
        return round(
            self.qb.points
            + self.wr1.points
            + self.wr2.points
            + self.rb1.points
            + self.rb2.points
            + self.te.points
            + self.flex.points,
            2,
        )


def player_with_max_points(list_of_players: List[BoxPlayer]) -> BoxPlayer:
    """Find player with max points in a list."""
    return list_of_players.pop(
        list_of_players.index(max(list_of_players, key=lambda x: x.points))
    )


def index_of_first_player_in_position(
    list_of_players: List[BoxPlayer], position: str
) -> int:
    """Return the index of the first player matching position."""
    return list_of_players.index(
        [x for x in list_of_players if position in x.eligibleSlots][0]
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


def replace_with_free_agent(
    ideal_lineup: IdealLineup, free_agent_list: List[BoxPlayer]
) -> IdealLineup:
    """Replace players with 0 points in lineup with free agents."""
    for dataclass_field in fields(ideal_lineup):
        if getattr(ideal_lineup, dataclass_field.name).points == 0:
            free_agent = free_agent_list.pop(
                index_of_first_player_in_position(
                    free_agent_list, dataclass_field.metadata["position"]
                )
            )
            setattr(ideal_lineup, dataclass_field.name, free_agent)

    return ideal_lineup


def get_best_ball_scores(league: League) -> pd.DataFrame:
    """Get best ball scores for weeks so far."""
    out = {}
    waiver_order: List[Team] = league.teams
    for week in range(1, league.current_week):
        out[f"Week {week}"] = {}

        box_scores = league.box_scores(week)
        teams = {}
        for box_score in box_scores:
            if box_score.home_team != 0:
                teams[box_score.home_team.team_name] = box_score.home_lineup

            if box_score.away_team != 0:
                teams[
                    box_score.away_team.team_name  # type: ignore
                ] = box_score.away_lineup

        free_agents: List[BoxPlayer] = sorted(
            [
                x
                for x in league.free_agents(week=week)
                if x.points > 0.0  # type: ignore
            ],
            key=lambda x: x.projected_points,  # type: ignore
        )[::-1]

        for team in waiver_order:
            ideal_lineup = create_ideal_lineup(teams[team.team_name])
            ideal_lineup_w_fa = replace_with_free_agent(ideal_lineup, free_agents)

            out[f"Week {week}"][team.team_name] = ideal_lineup_w_fa.total_points()

        total_score_order = list(pd.DataFrame(out).sum(axis=1).sort_values().index)
        waiver_order = sorted(
            waiver_order, key=lambda x: total_score_order.index(x.team_name)
        )

    return pd.DataFrame(out)


def main():
    """Run main function."""
    league = League(league_id=1030704919, year=2022)
    get_best_ball_scores(league).to_csv("hackathon_points.csv")


if __name__ == "__main__":
    main()
