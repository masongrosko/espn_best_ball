"""Validate draft order."""

import re
from pathlib import Path

import pandas as pd

base_path = Path(__file__).parent
# base_path = Path("./espn_best_ball/draft")
draft_order_csv_folder = base_path / "draft_order"
input_draft_order_html_folder = base_path / "input_draft_order"


def load_csv_draft_order(team: str) -> pd.DataFrame:
    """Load provided csv draft order."""
    df = pd.read_csv((draft_order_csv_folder / f"{team}.csv"))

    df["player_first_name"] = (
        df["player_first_name"]
        .str.replace(r"\s", "_", regex=True)
        .str.replace(r"\W", "", regex=True)
        .str.lower()
        .str.split("_")
        .str[0]
    )

    df["player_last_name"] = (
        df["player_last_name"]
        .str.replace(r"\s", "_", regex=True)
        .str.replace(r"\W", "", regex=True)
        .str.lower()
        .str.split("_")
        .str[0]
    )

    return df


def load_html_draft_order(team: str) -> pd.DataFrame:
    """Load html draft order from espn."""
    with open((input_draft_order_html_folder / f"{team}.html")) as f:
        html_table = f.read()

    rankings = []
    start_str = 'tabindex="0">'
    end_str = "</a>"
    for row in html_table.split("</tr>"):
        try:
            rankings.append(
                re.sub(
                    r"\s+",
                    "_",
                    (
                        re.findall(fr"{start_str}[^<]+{end_str}", row)[0]
                        .split(start_str)[1]
                        .split(end_str)[0]
                    ).lower(),
                )
            )
        except IndexError:
            break

    position = []
    start_str = 'playerpos ttu">'
    end_str = "</span>"
    for row in html_table.split("</tr>"):
        try:
            position.append(
                re.sub(
                    r"\s+",
                    "_",
                    (
                        re.findall(fr"{start_str}[^<]+{end_str}", row)[0]
                        .split(start_str)[1]
                        .split(end_str)[0]
                    ).lower(),
                )
            )
        except IndexError:
            break

    df = pd.DataFrame({"name": rankings, "position": position})
    df["name"] = (
        df["name"]
        .str.replace(r"\s", "_", regex=True)
        .str.replace(r"\W", "", regex=True)
        .str.lower()
        .str.split("_")
        .str[0:2]
        .str.join("_")
        .str.replace("gabe_davis", "gabriel_davis")
    )
    df["position_rank"] = df.groupby("position").cumcount() + 1

    return df


def too_many_ranked_ahead(
    csv_ranking: pd.DataFrame, number_of_teams: int = 9
) -> pd.Series:
    """Return a bool series indicating whether the player needs to be ranked."""
    return (
        csv_ranking["position"].str.upper().isin(["RB", "WR"])
        & (csv_ranking["position_rank"] > number_of_teams * 5)
    ) | (
        csv_ranking["position"].str.upper().isin(["QB", "TE"])
        & (csv_ranking["position_rank"] > number_of_teams * 2)
    )


def compare_rankings(csv_ranking: pd.DataFrame, html_ranking: pd.DataFrame):
    """Compare provided rankings to what is on espn."""
    csv_ranking = csv_ranking.dropna(how="all")
    csv_ranking = csv_ranking.loc[
        ~csv_ranking["position"].isin(["K", "D/ST", "DST", "DEF"])
    ]
    csv_ranking = csv_ranking.loc[~too_many_ranked_ahead(csv_ranking)].reset_index()
    html_ranking = html_ranking.loc[~too_many_ranked_ahead(html_ranking)].reset_index()

    name = (
        csv_ranking["player_first_name"].str.lower()
        + "_"
        + csv_ranking["player_last_name"].str.lower()
    )
    min_length = min(len(csv_ranking), len(html_ranking))
    test = name.iloc[0:min_length] != html_ranking.iloc[0:min_length]["name"]

    return pd.concat(
        [
            csv_ranking.iloc[0:min_length].loc[test],
            html_ranking.iloc[0:min_length].loc[test],
        ],
        axis=1,
    )


def main():
    """Run example script."""
    teams = [
        "andrew_r",
        "anthony_c",
        "caleb_f",
        "james_g",
        "john_b",
        "joseph_o",
        "landis_d",
        "leonardo_j",
        "mason_g",
    ]
    for team in teams:
        print("")
        csv_ranking = load_csv_draft_order(team)
        html_ranking = load_html_draft_order(team)

        x = compare_rankings(csv_ranking, html_ranking)
        print(x[["player_last_name", "position", "name"]])
