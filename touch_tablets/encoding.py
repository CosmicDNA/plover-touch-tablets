import urllib.parse


def encode_raw_url(url: str) -> str:
    return urllib.parse.quote(url, safe="")
