# import libraries
import pandas as pd
import re
import math

PLAYER_RE = r'([A-Z].\s)\w+'

def _minute(play):
    """
    Get int of minute (out of 48) that it occurs in
    """
    minute = (12 - int(play['TIME'].split(':')[0])) + ((int(play['QUARTER']) - 1) * 12) - 1
    return minute


# define helper function s
def parse_play(play):
    """
    Parse play details from a play-by-play string describing a play.
    Assuming valid input, this function returns structured data in a dictionary
    describing the play. If the play detail string was invalid, this function
    returns None.
    :param details: detail string for the play
    :param is_hm: bool indicating whether the offense is at home
    :param returns: dictionary of play attributes or None if invalid
    :rtype: dictionary or None

    SOURCE: https://github.com/MikeRa1979/SportsScrape
    """
    if pd.isnull(play['SCORE']):
        return None
    elif pd.isnull(play['HOMEDESCRIPTION']):
        aw = True
        hm = False
        is_hm = False
        details = play['VISITORDESCRIPTION']
    else:
        hm = True
        aw = False
        is_hm = True
        details = play['HOMEDESCRIPTION']

    # if input isn't a string, return None
    if not details or not isinstance(details, basestring):
        return None


    p = {}
    p['detail'] = details
    p['home'] = hm
    p['away'] = aw
    p['is_home_play'] = is_hm
    p['minute'] = _minute(play)
    p['is_fga'] = None
    p['is_fgm'] = None
    p['is_three'] = None
    p['shot_dist'] = None
    p['is_assist'] = None
    p['assister'] = None
    p['is_block'] = None
    p['blocker'] = None

    # home roster
    hm_roster = ['put team','roster', 'here']

    # parsing field goal attempts
    shotRE = (r'(?P<shooter>{0}) (?P<is_fgm>makes|misses) '
              '(?P<is_three>2|3)\-pt shot').format(PLAYER_RE)
    distRE = r' (?:from (?P<shot_dist>\d+) ft|at rim)'
    assistRE = r' \(assist by (?P<assister>{0})\)'.format(PLAYER_RE)
    blockRE = r' \(block by (?P<blocker>{0})\)'.format(PLAYER_RE)
    shotRE = r'{0}{1}(?:{2}|{3})?'.format(shotRE, distRE, assistRE, blockRE)
    m = re.match(shotRE, details, re.IGNORECASE)
    if m:
        p['is_fga'] = True
        p.update(m.groupdict())
        p['is_fgm'] = p['is_fgm'] == 'makes'
        p['is_three'] = p['is_three'] == '3'
        p['is_assist'] = pd.notnull(p.get('assister'))
        p['is_block'] = pd.notnull(p.get('blocker'))

        return p

    return None

def _pbp_fga(game):
    """
    Scrape basketball reference game play-by-play by ID
    Args:
        game_ID (str): bball reference gameID
    Returns: None
        pickles pbp DataFrame to data directory
    """
    url = ('http://www.basketball-reference.com/boxscores/pbp/{ID}.html').format(ID=game)

    # read pandas dataframe straight from url
    # first table from url
    pbp = pd.read_html(url)[0]
    pbp.columns = pbp.iloc[1]
    pbp.columns = ['TIME', 'VISITORDESCRIPTION', 'VISITORRESULTS', 'SCORE', 'HOMERESULTS', 'HOMEDESCRIPTION']
    # remove columns row from data in dataframe
    pbp = pbp.drop(pbp.index[1])

    pbp['QUARTER'] = pbp.TIME.str.extract('(.*?)(?=Q)', expand=False).str[0]
    pbp['QUARTER'] = pbp['QUARTER'].fillna(method='ffill')
    pbp['GAME'] = game

    pbp = pbp.loc[~pbp.TIME.isin(['Time', '1st Q', '2nd Q', '3rd Q', '4th Q']), :]
    plays = []

    # for each row, parse play
    for ind, play in pbp.iterrows():
        play = parse_play(play)
        if play is None:
            continue
        else:
            plays.append(play)

    plays = pd.DataFrame(plays)
    return plays
