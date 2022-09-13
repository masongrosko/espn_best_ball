"""Create a draft order ranking."""

from io import StringIO
from typing import Sequence

import nfl_data_py as nfl
import pandas as pd

from ._adp_api import ADPRestApi


def main():
    """Run an example script."""
    # Previous year depth chart performance
    depth_chart_data = _get_depth_chart_data()
    fantasy_points = _get_fantasy_points()
    depth_with_points = _add_fantasy_points_to_depth_chart(
        depth_chart_data, fantasy_points
    )
    depth_chart_performance = _create_depth_chart_performance(depth_with_points)

    # Merge to current depth charts
    current_depth_charts = _get_current_depth_charts()
    depth_chart_perf_curr = _merge_current_depth_chart_to_depth_chart_performance(
        current_depth_charts, depth_chart_performance
    )

    # Add adp
    adp_data = _get_adp_data()
    depth_chart_perf_w_adp_curr = _merge_adp_data_and_depth_chart_performance_data(
        adp_data, depth_chart_perf_curr
    )

    # Create position ranking
    depth_chart_perf_w_adp_curr["position_rank"] = _create_position_ranking(
        position_col=depth_chart_perf_w_adp_curr["position"],
        ranking_factors=[
            depth_chart_perf_w_adp_curr["adp_position_rank"],
            depth_chart_perf_w_adp_curr["depth_position_rank"],
        ],
    )

    # Reduce data to make my life easier
    depth_chart_perf_w_adp_curr = _reduce_data(
        depth_chart_perf_w_adp_curr,
        league_size=9,
        position_limits={"RB": 5, "WR": 5, "QB": 2, "TE": 2},
    )

    # Clean up data to match submission requirements
    submission = _final_cleanup(depth_chart_perf_w_adp_curr)

    # Write out
    submission.to_csv("mason_g.csv", index=False)


TEAM_TO_TEAM_CODE = {
    "Arizona Cardinals": "ARI",
    "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LA",
    "Las Vegas Raiders": "LV",
    "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",
    "New England Patriots": "NE",
    "New Orleans Saints": "NO",
    "New York Giants": "NYG",
    "New York Jets": "NYJ",
    "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT",
    "Seattle Seahawks": "SEA",
    "San Francisco 49ers": "SF",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS",
}


def _get_depth_chart_data() -> pd.DataFrame:
    """Get the depth chart data."""
    depth_chart_2021 = nfl.import_depth_charts([2021])
    depth_chart_2021 = depth_chart_2021.loc[depth_chart_2021["week"] == 1]
    depth_chart_2021 = depth_chart_2021.loc[
        depth_chart_2021["depth_position"].isin(["QB", "TE", "RB", "WR"])
    ]
    depth_chart_2021 = depth_chart_2021[
        ["gsis_id", "club_code", "depth_position", "depth_team"]
    ]

    return depth_chart_2021


def _get_fantasy_points() -> pd.DataFrame:
    """Get fantasy points."""
    fantasy_points_2021 = nfl.import_seasonal_data([2021])
    fantasy_points_2021 = fantasy_points_2021[["player_id", "fantasy_points_ppr"]]

    return fantasy_points_2021


def _add_fantasy_points_to_depth_chart(
    depth_chart: pd.DataFrame, fantasy_points: pd.DataFrame
) -> pd.DataFrame:
    """Add fantasy points to the depth chart."""
    depth_chart = depth_chart.merge(
        fantasy_points, left_on="gsis_id", right_on="player_id", how="left"
    )
    depth_chart = depth_chart.sort_values(by="fantasy_points_ppr", ascending=False)
    return depth_chart


def _create_depth_chart_performance(depth_chart: pd.DataFrame) -> pd.DataFrame:
    """Create depth chart performance statistics."""
    depth_chart_performance = pd.DataFrame()
    positions = ["RB", "WR", "QB", "TE"]
    for position in positions:
        subset = depth_chart.loc[depth_chart["depth_position"] == position]
        depth_chart_performance = pd.concat([depth_chart_performance, subset])

    depth_chart_performance = depth_chart_performance.reset_index(drop=True)
    depth_chart_performance["depth_team"] = depth_chart_performance[
        "depth_team"
    ].astype(int)
    depth_chart_performance["depth_team"] += depth_chart_performance.groupby(
        ["club_code", "depth_position", "depth_team"]
    ).cumcount()

    return depth_chart_performance


def _get_current_depth_charts() -> pd.DataFrame:
    """Get current depth charts."""
    with open("espn_best_ball/my_order/data/2022_depth_charts.csv") as f:
        df = f.read()

    corrected_file = ""
    teams = df.split('\n""\n')
    for team in teams:
        team_name = team.split("\n")[0]
        team_data = f"\n{team_name}," + f"\n{team_name},".join(team.split("\n")[1:])
        corrected_file += team_data

    df = pd.read_csv(
        StringIO(corrected_file),
        names=[
            "team",
            "qb_rank",
            "qb",
            "rb_rank",
            "rb",
            "wr_rank",
            "wr",
            "te_rank",
            "te",
        ],
    )
    df["depth"] = df["team"] == df["team"].shift()
    df["depth"] = df.groupby("team")["depth"].cumsum()

    df["team"] = df["team"].map(TEAM_TO_TEAM_CODE)

    stacked_df = pd.DataFrame()
    columns = ["qb", "rb", "wr", "te"]
    for col in columns:
        position_df = df[["team", col, "depth"]].copy()
        position_df["position"] = col.upper()
        position_df = position_df.rename({col: "name"}, axis=1)

        stacked_df = pd.concat([stacked_df, position_df])

    stacked_df = stacked_df.dropna()
    stacked_df["depth"] = stacked_df["depth"].astype(str)

    return stacked_df


def _merge_current_depth_chart_to_depth_chart_performance(
    current_depth_chart: pd.DataFrame, depth_chart_performance: pd.DataFrame
) -> pd.DataFrame:
    """Merge current depth chart to depth chart performance."""
    depth_chart_performance["depth_team"] = depth_chart_performance[
        "depth_team"
    ].astype(str)

    depth_chart_performance = depth_chart_performance.merge(
        current_depth_chart,
        left_on=["club_code", "depth_position", "depth_team"],
        right_on=["team", "position", "depth"],
        how="left",
    )

    # Cleanup
    depth_chart_performance = depth_chart_performance[
        ["name", "team", "position"]
    ].copy()
    depth_chart_performance = depth_chart_performance.loc[
        ~depth_chart_performance[["name", "team"]].duplicated()
    ]
    depth_chart_performance["name"] = (
        depth_chart_performance["name"]
        .str.replace(r"\s", "_", regex=True)
        .str.replace(r"\W", "", regex=True)
        .str.lower()
        .str.split("_")
        .str[0:2]
        .str.join("_")
    )
    depth_chart_performance["player_first_name"] = (
        depth_chart_performance["name"].str.split("_").str[0]
    )
    depth_chart_performance["player_last_name"] = (
        depth_chart_performance["name"].str.split("_").str[1]
    )
    depth_chart_performance["team_name"] = depth_chart_performance["team"]
    depth_chart_performance["depth_position_rank"] = (
        depth_chart_performance.groupby(["position"]).cumcount() + 1
    )

    return depth_chart_performance


def _get_adp_data() -> pd.DataFrame:
    """Get adp data."""
    adp_data = ADPRestApi(
        scoring_format="ppr", year=2022, number_of_teams=12, position="ALL"
    ).get()
    adp_df = pd.DataFrame(adp_data)

    adp_data_standard = ADPRestApi(
        scoring_format="standard", year=2022, number_of_teams=12, position="ALL"
    ).get()
    adp_df_standard = pd.DataFrame(adp_data_standard)

    adp_df_standard = adp_df_standard.loc[
        ~adp_df_standard["name"].isin(adp_df["name"].unique())
    ]
    adp_df = pd.concat([adp_df, adp_df_standard])

    adp_df = adp_df[["name", "position", "adp"]].copy()
    adp_df["name"] = (
        adp_df["name"]
        .str.replace(r"\s", "_", regex=True)
        .str.replace(r"\W", "", regex=True)
        .str.lower()
        .str.split("_")
        .str[0:2]
        .str.join("_")
    )
    adp_df = adp_df.sort_values(by="adp", ascending=True)
    adp_df["adp_position_rank"] = adp_df.groupby("position").cumcount() + 1

    return adp_df


def _merge_adp_data_and_depth_chart_performance_data(
    adp_data: pd.DataFrame, depth_chart_performance: pd.DataFrame
) -> pd.DataFrame:
    """Merge adp_data and depth_chart performance data."""
    depth_with_adp = depth_chart_performance.merge(adp_data, on=["name", "position"])

    return depth_with_adp


def _create_position_ranking(
    position_col: pd.Series, ranking_factors: Sequence[pd.Series]
) -> pd.Series:
    """Create position rankings from provided ranking factors."""
    position_rank_average = pd.DataFrame(ranking_factors).mean(axis=1)
    position_rank_average = position_rank_average.sort_values()

    return position_rank_average.groupby(position_col).cumcount() + 1


def _reduce_data(
    data: pd.DataFrame, position_limits: dict, league_size: int
) -> pd.DataFrame:
    """Reduce data to make my life easier."""
    submission = pd.DataFrame()

    for position, limit in position_limits.items():
        x = data.loc[data["position"] == position]
        submission = pd.concat([submission, x.iloc[: (limit * league_size)]])

    return submission


def _final_cleanup(submission: pd.DataFrame) -> pd.DataFrame:
    """Final cleanup."""
    submission["overall_rank"] = submission["position_rank"].notna().cumsum()

    # Final submission
    return submission[
        [
            "player_first_name",
            "player_last_name",
            "team_name",
            "position",
            "overall_rank",
            "position_rank",
        ]
    ]
