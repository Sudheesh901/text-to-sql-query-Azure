import os

import requests


API_BASE_URL = os.getenv("BEAVELO_API_URL", "http://127.0.0.1:8000")


class BeaveloAPIError(Exception):
    """Raised when the Beavelo API cannot be reached or returns an error."""


def ask_beavelo(question: str) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/query",
            json={"question": question},
            timeout=45,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise BeaveloAPIError(
            "Beavelo is temporarily unavailable. Please try again."
        ) from error