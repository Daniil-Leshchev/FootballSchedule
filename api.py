import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from main import create_events_list
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json

from colorama import init, Fore
init(autoreset=True)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = 'g22faufip96tqjv8cjv6cflt00@group.calendar.google.com'

def create_gcal_event(match):
    return {
        'summary': match['summary'],

        'start': {
            'dateTime': match['start_time']
        },

        'end': {
            'dateTime': match['end_time']
        }
    }

def select_month_matches(service, months):
    now = parse_date(str(datetime.now()))
    start = now + relativedelta(
        month=int(months[0]), day=1, year=now.year,
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + relativedelta(months=+len(months))

    timezone = None
    try:
        with open('config.json', 'r') as f:
            timezone = json.load(f)['timezone']
    except (FileNotFoundError, json.JSONDecodeError):
        raise ValueError('Timezone cannot be read from your config file, try again')
    events = service.events().list(
        calendarId=CALENDAR_ID, orderBy='startTime',
        singleEvents=True, timeMin=start.isoformat() + timezone, 
        timeMax=end.isoformat() + timezone
    ).execute()
    return events['items']

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        matches, selected_months = create_events_list()
        if matches == []:
            print(Fore.LIGHTRED_EX + 'No events found')
            return

        potential_duplicates = select_month_matches(service, selected_months)
        count_duplicates = 0
        for match in matches:
            for potential_duplicate in potential_duplicates:
                if match['summary'] == potential_duplicate['summary']:
                    possible_dates = []
                    match_date = parse_date(match['start_time']).date()
                    for delta in range(-1, 2):
                        possible_dates.append((match_date + relativedelta(days=+delta)).strftime('%Y-%m-%d'))
                    potential_duplicate_date = parse_date(potential_duplicate['start']['dateTime']).date()
                    if str(potential_duplicate_date) in possible_dates:
                        print(Fore.LIGHTYELLOW_EX + f'Duplicate found {potential_duplicate['summary'], potential_duplicate['start']['dateTime']}')
                        count_duplicates += 1
                        break
            else:
                service.events().insert(calendarId=CALENDAR_ID, body=create_gcal_event(match)).execute()
        
        matches_added = len(matches) - count_duplicates
        if matches_added == 0:
            print(Fore.LIGHTRED_EX + 'No events were added')
        elif matches_added == 1:
            print(Fore.GREEN + '1 event was successfully created')
        else:
            print(Fore.GREEN + f'{matches_added} events were successfully created')

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()