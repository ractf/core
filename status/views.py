from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.db import connection
import redis
import os
import requests
import psycopg2

from backend import settings
from backend.response import FormattedResponse
from config import config


class StatusView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        connection_info = []

        redis_status, redis_details = self.test_redis_connection()
        connection_info.append({"name": "Redis", "status": redis_status, "details": redis_details})

        postgres_status, postgres_details = self.test_postgresql_connection()
        connection_info.append({"name": "PostgreSQL", "status": postgres_status, "details": postgres_details})

        andromeda_status, andromeda_details = self.get_andromeda_status()
        connection_info.append({"name": "Andomeda", "status": andromeda_status, "details": andromeda_details})

        if settings.SEND_MAIL:
            mailusv_status, mailusv_details = self.test_mailusv_connection()
            connection_info.append({"name": "Mail Daemon", "status": mailusv_status, "details": mailusv_details})

        return FormattedResponse(connection_info)

    def test_redis_connection(self):
        status, details = 'unknown', ''

        try:
            rs_details = settings.CONFIG['REDIS']
            rs = redis.Redis(host=rs_details['HOST'], port=rs_details['PORT'])

            if rs.ping() == True:
                status = 'online'
            else:
                status = 'offline'
                details = "PING failed"
        except redis.exceptions.RedisError as e:
            status = 'offline'
            details = "PING failed:\n" + str(e)

        return status, details

    def test_postgresql_connection(self):
        status, details = 'unknown', ''

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1");
            status = 'online'
        except psycopg2.OperationalError as e:
            status = 'offline'
            details = 'Could not execute query `SELECT 1\':\n' + str(e)
        
        return status, details

    def get_andromeda_status(self):
        status, details = 'unknown', ''
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
                    status = 'partial'
                    details = '\n'.join(reasons)
                else:
                    status = 'online'
            else:
                status = 'unknown'
                details = 'Error connecting to /status'
        except requests.exceptions.RequestException as e:
            status = 'offline'
            details = str(e)
        
        return status, details

    def test_mailusv_connection(self):
        status, details = 'unknown', ''

        try:
            response = requests.get(settings.MAIL_SOCK_URL)
            if response.status_code != 200:
                status = 'unknown'
                details = 'Unknown error whilst connecting to /'
            else:
                status = 'online'
        except requests.exceptions.RequestException as e:
            status = 'offline'
            details = str(e)
        
        return status, details
