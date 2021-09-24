"""

Some hints about the API response codes:
https://github.com/odota/web/blob/master/src/lang/en-US.json

"""

import json
import os
import pandas as pd
import requests
import time
from tqdm import tqdm


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


def get_mid_players(timestamp, n_recent, limit, start):
    if os.path.isfile('wl_n_{}_from_{}.csv'.format(n_recent, timestamp)):
        mid_players_df = pd.read_csv('wl_n_{}_from_{}.csv'.format(n_recent, timestamp))
        mid_players = list(mid_players_df['player_id'].astype(int))
    else:
        mid_players_df = pd.DataFrame(columns=['match_id', 'player_id', 'win_rate'])
        mid_players = []
    if os.path.isfile('pm_from_{}.json'.format(timestamp)):
        pm = json.loads(open('pm_from_{}.json'.format(timestamp), 'r').read())
    else:
        pm = requests.request("GET", pm_url.format(timestamp, LOBBY_ALL_DRAFT, GAME_MODE_RANKED, NUM_MMR_LOW_SKILL),
                              headers=headers, data=payload)
        pm = json.loads(pm.text)['rows']
        with open('pm_from_{}.json'.format(timestamp), 'w') as f:
            f.write(json.dumps(pm))
    counter = 0
    for it in tqdm(pm):
        counter += 1
        if counter < start:
            continue
        match = requests.request("GET", match_url.format(it['match_id']), headers=headers, data=payload)
        time.sleep(1)
        match = json.loads(match.text)
        try:
            for p in match['players']:
                if p['lane_role'] == MID_ROLE and p['account_id'] is not None \
                        and p['account_id'] not in mid_players and is_bad(p):
                    wl = get_wl(p['account_id'], it['match_id'], n_recent)
                    if wl:
                        mid_players_df = mid_players_df.append({'match_id': it['match_id'],
                                                                'player_id': p['account_id'],
                                                                'win_rate': wl / n_recent}, ignore_index=True,)
                        mid_players_df.to_csv('wl_n_{}_from_{}.csv'.format(n_recent, timestamp), index=False)
                        mid_players.append(p['account_id'])
                        if len(mid_players) == limit:
                            print('Limit of found players is reached')
                            return
        except KeyError:
            continue
    mid_players_df.to_csv('wl_n_{}_from_{}.csv'.format(n_recent, timestamp), index=False)


def get_wl(player_id, match_id, n_recent=10):
    rm = requests.request("GET", rm_url.format(player_id), headers=headers, data=payload)
    try:
        idx = [index for index, value in enumerate(json.loads(rm.text)) if value['match_id'] == match_id][0]
    except IndexError:
        return None
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


def is_bad(player, kd_th=1.5, gxp_th=500):
    return (player['deaths']+1)/(player['kills']+1) >= kd_th or \
           player['gold_per_min'] < gxp_th or player['xp_per_min'] < gxp_th


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
    # from_date = '2021-09-01T00:00:00.000Z'

    get_mid_players(from_date, n_recent, limit=500, start=7008)

