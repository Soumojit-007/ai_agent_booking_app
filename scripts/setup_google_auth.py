#!/usr/bin/env python3
"""
Google Calendar API Setup Script
This script helps set up Google Calendar API authentication.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def setup_google_calendar_auth():
    """Set up Google Calendar API authentication."""
    print("🔧 Setting up Google Calendar API authentication...")
    
    # Check if credentials file exists
    credentials_path = r"C:\Users\DELL\OneDrive\Desktop\AI-Booking agent app\credentials\google_credentials.json"

    if not os.path.exists(credentials_path):
        print(f"❌ Google credentials file not found at {credentials_path}")
        print("\n📋 To set up Google Calendar API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Calendar API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the JSON file and save it as 'credentials/google_credentials.json'")
        return False
    
    creds = None
    token_path = 'token.pickle'
    
    # Load existing token
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=8000)
        
        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    # Test the credentials
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar_list = service.calendarList().list().execute()
        print("✅ Successfully connected to Google Calendar!")
        print(f"📅 Found {len(calendar_list.get('items', []))} calendars")
        
        for calendar in calendar_list.get('items', []):
            print(f"  - {calendar['summary']} ({calendar['id']})")
        
        return True
    
    except Exception as e:
        print(f"❌ Error testing Google Calendar connection: {e}")
        return False

if __name__ == "__main__":
    # Create credentials directory if it doesn't exist
    os.makedirs("credentials", exist_ok=True)
    
    success = setup_google_calendar_auth()
    if success:
        print("\n🎉 Google Calendar setup completed successfully!")
        print("You can now run the booking agent.")
    else:

        print("\n❌ Setup failed. Please check the instructions above.")




