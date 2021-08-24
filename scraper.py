"""

Some hints about the API response codes:
https://github.com/odota/web/blob/master/src/lang/en-US.json

"""

'''

* fetch public matches starting from a fixed date and withing a certain MMR range
* get data about found matches
* if exposed player is found with lane_role = 2
    * get info about his N most recent matches

'''

import json
import requests

MID_ROLE = 2

pm_url = "https://api.opendota.com/api/explorer?sql=SELECT * \
    FROM public_matches \
    WHERE public_matches.start_time >= extract(epoch from timestamp '2021-08-21T00:00:00.000Z') \
    AND public_matches.lobby_type = 7 AND public_matches.game_mode = 22 AND public_matches.num_mmr = 2"

match_url = "https://api.opendota.com/api/matches/{}"

payload = {}
headers = {}

if __name__ == '__main__':

    mid_players = []

    pm = requests.request("GET", pm_url, headers=headers, data=payload)
    pm = json.loads(pm.text)['rows']
    for it in pm:
        match = requests.request("GET", match_url.format(it['match_id']), headers=headers, data=payload)
        match = json.loads(match.text)
        for p in match['players']:
            try:
                if p['lane_role'] == MID_ROLE and p['account_id'] is not None:
                    mid_players.append(p['account_id'])
                    break
            except KeyError:
                continue
