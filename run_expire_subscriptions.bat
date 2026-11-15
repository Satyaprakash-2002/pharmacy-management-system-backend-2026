@echo off
cd /d "C:\pharmacy-management-system-backend"
"C:\pharmacy-management-system-backend\venv\Scripts\python.exe" manage.py expire_subscriptions >> "C:\pharmacy-management-system-backend\expire_subscriptions.log" 2>&1
