import requests as req
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

page = req.get('https://www.skysports.com/real-madrid-fixtures')
page_parsed = BeautifulSoup(page.content, 'html.parser')

matches = page_parsed.find_all('div', class_='fixres__item')
data = []

def get_match_date(match):
    date = match.find_previous_sibling('h4', class_='fixres__header2').text.strip()
    year = match.find_previous_sibling('h3', class_='fixres__header1').text[-4:]
    time = match.find('span', class_='matches__date').text.strip()
    full_date = f'{date} {year} {time}'

    return parse_date(full_date)