import requests as req
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
import datetime

FAV_TEAM = 'Real Madrid'
now = datetime.datetime.now()
next_month = f'0{now.month + 1}'

def get_matches():
    page = req.get('https://www.skysports.com/real-madrid-fixtures')
    page_parsed = BeautifulSoup(page.content, 'html.parser')
    return page_parsed.find_all('div', class_='fixres__item')

def get_match_datetime(match):
    date = match.find_previous_sibling('h4', class_='fixres__header2').text.strip()
    year = match.find_previous_sibling('h3', class_='fixres__header1').text[-4:]
    time = match.find('span', class_='matches__date').text.strip()
    full_date = f'{date} {year} {time}'

    start_time = parse_date(full_date)
    end_time = start_time + relativedelta(hours=+2)

    return (start_time.isoformat(), end_time.isoformat())

def get_opponent(match, fav_team):
    teams = match.find_all('span', class_='swap-text__target')
    if teams[0].text.strip() == fav_team:
        return teams[1].text.strip()
    return teams[0].text.strip()

def create_events_list():
    matches_list = []
    for match in get_matches():
        date = get_match_datetime(match)
        if date[0][5:7] != next_month:
            continue

        matches_list.append({
            'summary': f'{FAV_TEAM} vs {get_opponent(match, FAV_TEAM)}',
            'start_time': date[0] + '+01:00',
            'end_time': date[1] + '+01:00'
        })

    return matches_list