import os
import json
import requests
from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Google Calendar API 설정
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'your-service-account-file.json'  # 다운로드한 서비스 계정 JSON 파일 경로
CALENDAR_ID = 'primary'  # 기본 캘린더 사용

# Slack Webhook URL
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/your/webhook/url'  # 슬랙 Webhook URL

# Google Calendar에서 일정 가져오기
def get_calendar_events(date):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    
    # 날짜 범위 설정 (KST 시간대 사용)
    start_time = datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)
    end_time = start_time + timedelta(days=1)
    
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_time.isoformat(),
        timeMax=end_time.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    return events

# 이벤트를 Slack으로 전송하기
def send_to_slack(events, date):
    if not events:
        message = f"{date}에는 예정된 일정이 없습니다."
    else:
        message = f"{date} 예정된 일정:\n"
        for event in events:
            event_summary = event.get('summary', 'No Title')
            message += f"- {event_summary}\n"

    payload = {'text': message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    
    if response.status_code == 200:
        print("슬랙 메시지 전송 성공!")
    else:
        print(f"슬랙 메시지 전송 실패: {response.status_code}")

# Flask 서버 설정
from flask import Flask, request

app = Flask(__name__)

@app.route('/events', methods=['GET'])
def events():
    # 요청에서 날짜 받기 (예: /events?date=2025-05-12)
    date_str = request.args.get('date')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return "잘못된 날짜 형식입니다. 올바른 형식: YYYY-MM-DD", 400
    
    events = get_calendar_events(date)
    send_to_slack(events, date_str)
    return "Slack으로 일정 전송 완료", 200

if __name__ == '__main__':
    app.run(debug=True)
