import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from main import create_events_list
from main import SOURCE_TIMEZONE
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from datetime import datetime
from pytz import utc as UTC
from colorama import init, Fore
init(autoreset=True)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

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

def select_month_matches(service, months, calendar_id, first_event_year):
    now = parse_date(str(datetime.now()))
    start = now + relativedelta(
        month=int(months[0]), day=1, year=first_event_year,
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + relativedelta(months=+len(months))

    events = service.events().list(
        calendarId=calendar_id, orderBy='startTime',
        singleEvents=True, timeMin=start.isoformat() + SOURCE_TIMEZONE, 
        timeMax=end.isoformat() + SOURCE_TIMEZONE
    ).execute()
    return events['items']

def parse_datetime_utc(datetime_str):
    return parse_date(datetime_str).astimezone(UTC)

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        matches, selected_months, CALENDAR_ID, first_event_year = create_events_list()
        if matches == []:
            print(Fore.LIGHTRED_EX + 'No events found')
            return

        month_events = select_month_matches(service, selected_months, CALENDAR_ID, first_event_year)
        count_duplicates = 0
        count_updated = 0
        
        for match in matches:
            potential_duplicates = [event for event in month_events if parse_datetime_utc(event['start']['dateTime']).date() == parse_datetime_utc(match['start_time']).date()]
            for potential_duplicate in potential_duplicates:
                if match['summary'] == potential_duplicate['summary']:
                    match_start = parse_datetime_utc(match['start_time'])
                    match_end = parse_datetime_utc(match['end_time'])
                    potential_duplicate_start = parse_datetime_utc(potential_duplicate['start']['dateTime'])
                    potential_duplicate_end = parse_datetime_utc(potential_duplicate['end']['dateTime'])
                    
                    if match_start == potential_duplicate_start and match_end == potential_duplicate_end:  
                        print(Fore.LIGHTYELLOW_EX + f'Duplicate found: {potential_duplicate['summary'], potential_duplicate['start']['dateTime']}')
                        count_duplicates += 1
                        break

                    else:
                        event = service.events().get(calendarId=CALENDAR_ID, eventId=potential_duplicate['id']).execute()
                        event['start']['dateTime'] = match['start_time']
                        event['end']['dateTime'] = match['end_time']

                        updated_event = service.events().update(calendarId=CALENDAR_ID, eventId=event['id'], body=event).execute()
                        print(Fore.LIGHTMAGENTA_EX + f'Time for the match {match['summary']} has changed to {match_start}')
                        count_updated += 1
                        break
            else:
                service.events().insert(calendarId=CALENDAR_ID, body=create_gcal_event(match)).execute()
        
        matches_added = len(matches) - count_duplicates - count_updated
        if matches_added != 0:
            print(Fore.GREEN + f'{matches_added} events were successfully created')
        else:
            print(Fore.LIGHTRED_EX + 'No events were created')
        if count_updated != 0:
            print(Fore.LIGHTGREEN_EX + f'{count_updated} events were updated')

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()