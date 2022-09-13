"""ADP API."""
from typing import Mapping, Sequence, Union

import requests
from requests import Response

JsonLike = Union[Mapping, Sequence]


# ADP Rest API
class ADPRestApi:
    """Get the ADP values from drafts done on fantasyfootballcalculator.com."""

    def __init__(
        self, scoring_format="ppr", year=2022, number_of_teams=12, position="all"
    ):
        """Initialize a new ADPRestApi instance."""
        self.api_url = "https://fantasyfootballcalculator.com/api/v1/adp"
        self.scoring_format = self._get_valid_scoring_format(scoring_format)
        self.year = year
        self.number_of_teams = number_of_teams
        self.position = self._get_valid_position(position)

    def get(self) -> JsonLike:
        """Get call to ADP Rest API."""
        api_response = self._get()

        return self._remove_bad_data(api_response)

    def _get(self) -> Response:
        """Call API with get request."""
        return requests.request(
            method="GET",
            url=(
                f"{self.api_url}"
                f"/{self.scoring_format}"
                f"?year={self.year}"
                f"&teams={self.number_of_teams}"
                f"&position={self.position}"
            ),
        )

    def _remove_bad_data(self, response: Response, min_percentage: int = 1) -> JsonLike:
        """Remove the bad data from the response."""
        response_json: Mapping = response.json()
        total_drafts: int = response_json["meta"]["total_drafts"]
        min_value = total_drafts * (min_percentage / 100)

        return [x for x in response_json["players"] if x["times_drafted"] > min_value]

    def _get_valid_scoring_format(self, scoring_format: str) -> str:
        """Get a valid scoring format from the given scoring format."""
        valid_scoring_format = self.valid_scoring_formats.get(scoring_format.upper())

        if valid_scoring_format is None:
            raise ValueError(
                f"Invalid scoring format, expected one of the following: "
                f"{self.valid_scoring_formats.keys()} "
                f"received: {scoring_format}"
            )

        return valid_scoring_format

    def _get_valid_position(self, position: str) -> str:
        """Get a valid position from the given position."""
        valid_position = self.valid_positions.get(position.upper())

        if valid_position is None:
            raise ValueError(
                f"Invalid position, expected one of the following: "
                f"{self.valid_positions.keys()} "
                f"received: {position}"
            )

        return valid_position

    @property
    def valid_scoring_formats(self) -> Mapping:
        """Return a mapping of upper scoring formats to valid scoring formats."""
        return {
            "HALF-PPR": "half-ppr",
            "PPR": "ppr",
            "STANDARD": "standard",
            "ROOKIE": "rookie",
        }

    @property
    def valid_positions(self) -> Mapping:
        """Return a mapping of upper positions to valid positions."""
        return {
            "ALL": "all",
            "QB": "QB",
            "RB": "RB",
            "WR": "WR",
            "TE": "TE",
            "PK": "PK",
            "DEF": "DEF",
        }
