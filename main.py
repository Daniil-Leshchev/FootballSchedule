import requests as req
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

import os.path
import re
import json

from colorama import init, Fore
init(autoreset=True)

def get_team_config():
    filename = 'config.json'

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    
    team = input(Fore.CYAN + 'Type in your team to follow: ')
    timezone = input(Fore.CYAN + "Choose your team timezone in format: '+00:00' relative to UTC time: ")
    print()
    json_data = {
        'team': team,
        'timezone': timezone
    }

    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=4)
    return json_data

def create_page_link(team):
    return f'https://www.skysports.com/{team.replace(' ', '-').lower()}-fixtures'

def convert_month_name_to_number(month_name):
    months = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October":  10,
        "November": 11,
        "December": 12
    }

    try:
        return months[month_name.capitalize()]

    except KeyError:
        raise ValueError(Fore.LIGHTRED_EX + f"Invalid month name, check your spelling: {month_name}")

def format_month_number(month_number):
    return f'0{month_number}' if len(str(month_number)) == 1 else str(month_number)

def select_months():
    print('Please select months to load data from')
    print("It can be a single month in format 'August' or several months in format 'August-December'")
    selected_month_range = input(Fore.CYAN + 'Month(s): ')

    if selected_month_range == '':
        raise ValueError(Fore.LIGHTRED_EX + 'Empty user input')

    selected_months = []
    if '-' in selected_month_range:
        start, end = selected_month_range.split('-')
        start_month_number = convert_month_name_to_number(start)
        end_month_number = convert_month_name_to_number(end)

        if start_month_number >= end_month_number:
            raise ValueError(Fore.LIGHTRED_EX + 'Start month number cannot be more than(or equal) end month')

        for month_number in range(start_month_number, end_month_number + 1):
            selected_months.append(format_month_number(month_number))
    else:
        selected_months.append(format_month_number(convert_month_name_to_number(selected_month_range)))

    return selected_months

def get_matches(user_team):
    try:
        page = req.get(create_page_link(user_team))
        page_parsed = BeautifulSoup(page.content, 'html.parser')

        if page_parsed.find('div', class_='not-found'):
            raise ValueError(Fore.LIGHTRED_EX + 'Your team is not found, check your spelling in the configuration')

        return page_parsed.find_all('div', class_='fixres__item')
    except req.exceptions.RequestException as error:
        print(f'Error occured while parsing the source site {error}')

def get_match_datetime(match, timezone):
    date = match.find_previous_sibling('h4', class_='fixres__header2').text.strip()
    year = match.find_previous_sibling('h3', class_='fixres__header1').text[-4:]
    time = match.find('span', class_='matches__date').text.strip()
    full_date = f'{date} {year} {time}'

    start_time = parse_date(full_date)
    end_time = start_time + relativedelta(hours=+2)#setting match duration

    return (start_time.isoformat() + timezone, end_time.isoformat() + timezone)

def get_opponent(match, user_team):
    teams = match.find_all('span', class_='swap-text__target')
    if teams[0].text.strip() == user_team:
        return teams[1].text.strip()
    return teams[0].text.strip()

def create_events_list():
    config_results = get_team_config()
    user_team = config_results['team']
    user_timezone = config_results['timezone']

    if user_team == '':
        os.remove('config.json')
        raise ValueError(Fore.LIGHTRED_EX + 'No team specified')
    
    if re.match(r"^[+-]\d{1,2}:\d{2}$", user_timezone) is None:#check if user_timezone is specified correctly via regex
        os.remove('config.json')
        raise ValueError(Fore.LIGHTRED_EX + 'Invalid timezone')

    matches_list = []
    selected_months = select_months()

    for match in get_matches(user_team):
        date = get_match_datetime(match, user_timezone)
        month_number = date[0][5:7]
        if month_number not in selected_months:
            continue

        matches_list.append({
            'summary': f'{user_team} vs {get_opponent(match, user_team)}',
            'start_time': date[0],
            'end_time': date[1]
        })

    return matches_list, selected_months