from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from django.db import connection
import redis
import os
import requests

from backend import settings
from backend.response import FormattedResponse
from config import config

@api_view(['GET'])
@permission_classes([IsAdminUser])
def status(request):

    data = [
        {
            "name": "Redis",
            "status": "unknown",
            "details": ''
        },
        {
            "name": "PostgreSQL",
            "status": "unknown",
            "details": ''
        },
        {
            "name": "Andromeda",
            "status": "unknown",
            "details": ''
        }]

    # Test redis connection
    try:
        rs_details = settings.CONFIG['REDIS']
        rs = redis.Redis(host=rs_details['HOST'], port=rs_details['PORT'])
        if rs.ping() == True:
            data[0]['status'] = 'online'
        else:
            data[0]['status'] = 'offline'
            data[0]['details'] = "PING failed"
    except Exception as e:
        data[0]['status'] = 'offline'
        data[0]['details'] = "PING failed"


    # Test postgresql connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1");
        data[1]['status'] = 'online'
    except:
        data[1]['status'] = 'offline'
        data[1]['details'] = 'Could not execute query `SELECT 1\''

    try:
        response = requests.get(f"{settings.CHALLENGE_SERVER_URL}/status",
                            headers={"Authorization": settings.CHALLENGE_SERVER_API_KEY})
        if response.status_code == 200:
            sysinfo = response.json()
            reasons = []
            if sysinfo['Loads'][0] > 90:
                reasons.append(f"High CPU load: {sysinfo['Loads'][0]}")
            if sysinfo['FreeRam'] / sysinfo['TotalRam'] < 0.2:
                reasons.append(f"High RAM usage: {sysinfo['FreeRam'] / 1024}MB free out of {sysinfo['TotalRam']}")
            if len(reasons) != 0:
                data[2]['status'] = 'partial'
                data[2]['details'] = '\n'.join(reasons)
            else:
                data[2]['status'] = 'online'
        else:
            data[2]['status'] = 'unknown'
            data[2]['details'] = 'Error connecting to /status'
    except Exception as e:
        data[2]['status'] = 'offline'
        data[2]['details'] = str(e)

    if settings.SEND_MAIL:
        data.append(
        {
            "name": "Mail Daemon",
            "status": "unknown",
            "details": ''
        })
        try:
            response = requests.get(settings.MAIL_SOCK_URL)
            if response.status_code != 200:
                data[3]['status'] = 'unknown'
                data[3]['details'] = 'Unknown error whilst connecting to /'
            else:
                data[3]['status'] = 'online'
        except Exception as e:
            data[3]['status'] = 'offline'
            data[3]['details'] = str(e)


    return FormattedResponse(data)
