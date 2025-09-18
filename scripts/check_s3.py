import datetime
import datetime as dt
import os
from textwrap import shorten

import boto3
import botocore


def check_s3_ingest():
    endpoint = os.getenv("S3_ENDPOINT")
    bucket = os.getenv("S3_BUCKET_RAW")
    if not endpoint or not bucket:
        raise SystemExit(
            "Missing S3_ENDPOINT or S3_BUCKET_RAW in scheduler env."
        )

    s3 = boto3.client("s3", endpoint_url=endpoint)
    ds = dt.datetime.now(tz=datetime.UTC).date().isoformat()
    prefixes = [
        "geo.getTopArtists",
        "geo.getTopTracks",
        "chart.getTopArtists",
        "chart.getTopTracks",
        "user.getRecentTracks",
    ]

    for pref in prefixes:
        pfx = f"{pref}/dt={ds}/"
        try:
            r = s3.list_objects_v2(Bucket=bucket, Prefix=pfx, MaxKeys=5)
            n = r.get("KeyCount", 0)
            print(f"{pfx} -> {n} object(s)")
            if n and "Contents" in r:
                k = r["Contents"][0]["Key"]
                body = (
                    s3.get_object(Bucket=bucket, Key=k)["Body"]
                    .read(1200)
                    .decode("utf-8", "ignore")
                )
                print(" sample key:", k)
                print(
                    " sample json:",
                    shorten(body, width=400, placeholder="..."),
                    "\n",
                )
        except botocore.exceptions.ClientError as e:
            msg = e.response.get("Error", {}).get("Message", str(e))
            print(f"{pfx} -> ERROR: {msg}")
        except Exception as e:
            print(f"{pfx} -> ERROR: {e}")


if __name__ == "__main__":
    check_s3_ingest()
