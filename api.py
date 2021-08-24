"""

Some hints about the API response codes:
https://github.com/odota/web/blob/master/src/lang/en-US.json

"""

import csv
import json
import requests

MID_ROLE = 2
LOBBY_ALL_DRAFT = 7
GAME_MODE_RANKED = 22
NUM_MMR_LOW_SKILL = 2

pm_url = "https://api.opendota.com/api/explorer?sql=SELECT * \
    FROM public_matches \
    WHERE public_matches.start_time >= extract(epoch from timestamp {}) \
    AND public_matches.lobby_type = {} AND public_matches.game_mode = {} AND public_matches.num_mmr = {}"

match_url = "https://api.opendota.com/api/matches/{}"

rm_url = "https://api.opendota.com/api/players/{}/recentMatches"

payload = {}
headers = {}


def get_mid_players(timestamp):
    mid_players = []
    pm = requests.request("GET", pm_url.format(timestamp, LOBBY_ALL_DRAFT, GAME_MODE_RANKED, NUM_MMR_LOW_SKILL), headers=headers, data=payload)
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
    return mid_players


def get_wl(player_id, n_recent=10):
    rm = requests.request("GET", rm_url.format(player_id), headers=headers, data=payload)
    rm = json.loads(rm.text)[:n_recent]
    if all([it['lobby_type']==7 and it['game_mode']==22 for it in rm]):
        return sum(
            [(it['radiant_win'] and it['player_slot'] in [1, 2, 3, 4, 5]) or
             (not(it['radiant_win']) and it['player_slot'] not in [1, 2, 3, 4, 5]) for it in rm]
        )


if __name__ == '__main__':

    '''
    * fetch public matches starting from a fixed date, within a certain MMR range, game mode Ranked and lobby type All Draft
    * get data about found matches
    * if exposed player is found with lane_role = 2
        * get info about his N most recent matches
        * if the N matches are all Ranked and All Draft, return win rate
    '''
    n_recent = 10
    from_date = '2021-08-21T00:00:00.000Z'
    wl = []
    players = get_mid_players(from_date)
    for it in players:
        wl.append(get_wl(it, n_recent))
    with open('wl_n_{}_from_{}.csv'.format(n_recent, from_date), 'w', newline='') as f:
        wr = csv.writer(f, quoting=csv.QUOTE_ALL)
        wr.writerow(wl)
