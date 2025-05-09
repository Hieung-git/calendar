from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'charged-chain-442610-k7-7697a201c316.json'
CALENDAR_ID = 'solbox.com_dppveauh7fmtabefn11oc0gh1s@group.calendar.google.com'

def get_calendar_events(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return [], "날짜 형식이 잘못되었습니다. (예: 2025-05-12)"
    
    tz = timezone(timedelta(hours=9))  # KST
    start = datetime.combine(date, datetime.min.time()).replace(tzinfo=tz)
    end = datetime.combine(date, datetime.max.time()).replace(tzinfo=tz)
    
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', []), None

@app.route('/slack/calendar', methods=['POST'])
def calendar_handler():
    text = request.form.get('text')  # 입력된 날짜 문자열
    user = request.form.get('user_name')

    events, error = get_calendar_events(text.strip())

    if error:
        return jsonify({'text': error}), 200

    if not events:
        return jsonify({'response_type': 'in_channel', 'text': f"{text} 일정 없음"}), 200

    message = f"*{text} 일정:*\n"
    for event in events:
        summary = event.get('summary', '제목 없음')
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        message += f"- {summary} ({start_time})\n"

    return jsonify({'response_type': 'in_channel', 'text': message}), 200

if __name__ == '__main__':
    app.run(debug=True)
