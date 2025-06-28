import pickle
import os
from datetime import datetime , timedelta
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import settings
import socket
from app.models.schemas import CalendarEvent , BookingRequest , AvailabilitySlot

SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarService():
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        token_path = 'token.pickle'

        # Wait for network
        def wait_for_internet(host="www.googleapis.com", timeout=3):
            while True:
                try:
                    socket.gethostbyname(host)
                    print("✅ Internet is available.")
                    return
                except:
                    print("🌐 Waiting for internet connection...")
                    time.sleep(timeout)

        wait_for_internet()
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                for attempt in range(3):  # Retry 3 times
                    try:
                        creds.refresh(Request())
                        print("✅ Token refreshed successfully.")
                        break
                    except Exception as e:
                        print(f"⚠️ Attempt {attempt+1} failed to refresh token: {e}")
                        time.sleep(2 ** attempt)
                else:
                    raise ConnectionError("❌ Could not refresh Google credentials after 3 attempts.")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Get events from calendar within date range"""
        try:
            events_result = self.service.events().list(
                calendarId=settings.google_calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            calendar_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                if 'T' in start:  # datetime format
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                else:  # date format
                    continue  # Skip all-day events
                
                calendar_events.append(CalendarEvent(
                    id=event['id'],
                    title=event.get('summary', 'No Title'),
                    start=start_dt,
                    end=end_dt,
                    description=event.get('description'),
                    location=event.get('location')
                ))
            
            return calendar_events
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def find_available_slots(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        duration_minutes: int = 60,
        working_hours_start: int = 9,
        working_hours_end: int = 17
    ) -> List[AvailabilitySlot]:
        """Find available time slots"""
        
        # Get existing events
        existing_events = self.get_events(start_date, end_date)
        
        available_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Create working hours for this day
            day_start = datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_start))
            day_end = datetime.combine(current_date, datetime.min.time().replace(hour=working_hours_end))
            
            # Get events for this day
            day_events = [
                event for event in existing_events 
                if event.start.date() == current_date
            ]
            
            # Sort events by start time
            day_events.sort(key=lambda x: x.start)
            
            # Find gaps between events
            current_time = day_start
            
            for event in day_events:
                # Check if there's a gap before this event
                if (event.start - current_time).total_seconds() >= duration_minutes * 60:
                    available_slots.append(AvailabilitySlot(
                        start=current_time,
                        end=event.start,
                        duration_minutes=int((event.start - current_time).total_seconds() / 60)
                    ))
                
                current_time = max(current_time, event.end)
            
            # Check for availability after the last event
            if (day_end - current_time).total_seconds() >= duration_minutes * 60:
                available_slots.append(AvailabilitySlot(
                    start=current_time,
                    end=day_end,
                    duration_minutes=int((day_end - current_time).total_seconds() / 60)
                ))
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def create_event(self, booking: BookingRequest) -> Optional[str]:
        """Create a calendar event"""
        try:
            event = {
                'summary': booking.title,
                'description': booking.description,
                'start': {
                    'dateTime': booking.start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': booking.end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if booking.location:
                event['location'] = booking.location
            
            if booking.attendees:
                event['attendees'] = [{'email': email} for email in booking.attendees]
            
            created_event = self.service.events().insert(
                calendarId=settings.google_calendar_id, 
                body=event
            ).execute()
            
            return created_event.get('id')
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

# Global instance
calendar_service = CalendarService()
