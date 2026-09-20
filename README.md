# Employee Attendance System

CSE 3206 | Software Engineering Sessional  
Group: 09 | Section: C2 | Team: M/I/R

## Project

Employee Attendance System built with:

- Flask backend
- React + Vite frontend
- PostgreSQL database
- Waterfall process model

## Roles

- Administrator / HR
- Employee

## Main Features

- Admin/employee login
- Department and employee management
- Daily check-in / check-out
- Attendance history and work minutes
- Leave request and approval
- Dashboard counts
- Illustrative monthly attendance-based salary summary

## Team Responsibilities

- M: Flask backend, authentication, REST API, GitHub repository setup
- I: React JSX frontend and API integration
- R: PostgreSQL, models, admin setup, migrations, data verification

## Local Setup Summary

### Backend

```powershell
cd backend
py -m venv .venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your local values
.\venv\Scripts\flask.exe --app wsgi db upgrade
.\venv\Scripts\flask.exe --app wsgi init-admin --email admin@lab.local
.\venv\Scripts\flask.exe --app wsgi run --port 5000
