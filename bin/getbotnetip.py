"""
Get botnet IPs from feodo tracker
Usage: "| getbotnetip | outputlookup override_if_empty=false botnet_ip.csv"
Recommend to update the lookup file every 5 minutes (cron "*/5 * * * *")
"""

import sys
from datetime import datetime, timezone
from os import path
from re import search
from time import time as unix_time

sys.path.insert(0, path.join(path.dirname(__file__)))
from utils import Utility

sys.path.insert(0, path.join(path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import Configuration, GeneratingCommand, Option, dispatch

DOWNLOAD_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.csv"


@Configuration()
class GetBotnetIP(Utility, GeneratingCommand):
    """Defines a search command that generates event records"""

    custom_message = Option(name="message")

    def generate(self):
        feodo_csv = self.download(DOWNLOAD_URL)
        updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # parse updated time from header comment
        for line in filter(lambda row: row[0] == "#", feodo_csv.splitlines()):
            if line.startswith("# Last updated:"):
                last_updated_utc = search(
                    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line
                ).group()
                updated = (
                    datetime.strptime(last_updated_utc, "%Y-%m-%d %H:%M:%S")
                    .replace(tzinfo=timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                break
        # parse input csv, remove '#' comments and output as events
        for row in self.csv_reader(feodo_csv):
            row["updated"] = updated
            if isinstance(self.custom_message, str) and len(self.custom_message) >= 1:
                row["custom_message"] = self.custom_message

            yield self.gen_record(_time=unix_time(), **row)


dispatch(GetBotnetIP, sys.argv, sys.stdin, sys.stdout, __name__)
