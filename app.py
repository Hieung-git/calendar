from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
import requests
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# Google Calendar 설정
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'charged-chain-442610-k7-7697a201c316.json'
CALENDAR_ID = 'ph702@solbox.com'

# Slack Webhook 설정
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'

def get_events_for_date(date_str):
    try:
        start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=9)))
        end = start.replace(hour=23, minute=59, second=59)
    except Exception as e:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])

def format_event(event):
    summary = event.get('summary', 'No Title')
    return re.sub(r'(CW-\d+)', r'<https://jira.solbox.com/browse/\1|\1>', summary)

def send_to_slack(date_str, events):
    if not events:
        message = f"{date_str} 예정된 일정이 없습니다."
    else:
        message = f"{date_str} 예정 작업 공유 드립니다.\n\n"
        for event in events:
            message += f"- {format_event(event)}\n"

    payload = {'text': message}
    return requests.post(SLACK_WEBHOOK_URL, json=payload)

@app.route("/events", methods=["GET"])
def handle_request():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Missing date=YYYY-MM-DD parameter"}), 400

    try:
        events = get_events_for_date(date_str)
        response = send_to_slack(date_str, events)
        return jsonify({"status": "ok", "slack_response": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
