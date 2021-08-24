"""

Some hints about the API response codes:
https://github.com/odota/web/blob/master/src/lang/en-US.json

"""

import csv
import json
import requests
import time

N_RECENT = 20
MID_ROLE = 2
LOBBY_ALL_DRAFT = 7
GAME_MODE_RANKED = 22
NUM_MMR_LOW_SKILL = 2

pm_url = "https://api.opendota.com/api/explorer?sql=SELECT * \
    FROM public_matches \
    WHERE public_matches.start_time >= extract(epoch from timestamp '{}') \
    AND public_matches.lobby_type = {} AND public_matches.game_mode = {} AND public_matches.num_mmr = {}"

match_url = "https://api.opendota.com/api/matches/{}"

rm_url = "https://api.opendota.com/api/players/{}/recentMatches"

payload = {}
headers = {}


def get_mid_players(timestamp, n_recent, limit):
    mid_players = []
    wl_list = []
    pm = requests.request("GET", pm_url.format(timestamp, LOBBY_ALL_DRAFT, GAME_MODE_RANKED, NUM_MMR_LOW_SKILL), headers=headers, data=payload)
    pm = json.loads(pm.text)['rows']
    with open('pm_from_{}.json'.format(timestamp), 'w') as f:
        f.write(json.dumps(pm))
    for it in enumerate(pm):
        print(it['match_id'])
        match = requests.request("GET", match_url.format(it['match_id']), headers=headers, data=payload)
        time.sleep(1)
        match = json.loads(match.text)
        for p in match['players']:
            try:
                if p['lane_role'] == MID_ROLE and p['account_id'] is not None and p['account_id'] not in mid_players:
                    wl = get_wl(p['account_id'],  it['match_id'], n_recent)
                    if wl:
                        mid_players.append(p['account_id'])
                        print("mids: {}".format(len(mid_players)))
                        wl_list.append(wl)
                        with open('wl_n_{}_from_{}.csv'.format(n_recent, timestamp), 'w', newline='') as f:
                            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
                            wr.writerow(wl)
                        with open('players_mid_low_skill.csv', 'w', newline='') as f:
                            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
                            wr.writerow(mid_players)
                        if len(mid_players == limit):
                          return
                    break
            except KeyError:
                continue


def get_wl(player_id, match_id, n_recent=10):
    rm = requests.request("GET", rm_url.format(player_id), headers=headers, data=payload)
    idx = [index for index, value in enumerate(rm) if value['match_id'] == match_id][0]
    if idx <= N_RECENT - n_recent:
        rm = json.loads(rm.text)[idx:idx+n_recent]
        if all([it['lobby_type'] == 7 and it['game_mode'] == 22 for it in rm]):
            return sum(
                [(it['radiant_win'] and it['player_slot'] in [1, 2, 3, 4, 5]) or
                 (not(it['radiant_win']) and it['player_slot'] not in [1, 2, 3, 4, 5]) for it in rm]
            )
        else:
            return None
    else:
        return None


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

    get_mid_players(from_date, n_recent, limit=500)

