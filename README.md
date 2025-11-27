# ELD Trip Planner

A full-stack application for truck driver Hours of Service (HOS) compliance and trip planning.

## Features

- Trip planning with HOS compliance
- Route optimization with required stops
- Daily log sheet generation
- 70-hour/8-day cycle tracking

## Tech Stack

- **Backend**: Django REST Framework
- **Frontend**: React with Material-UI
- **Database**: SQLite (development)

## Setup Instructions

### Backend Setup
1. Navigate to backend directory: `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate venv: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start server: `python manage.py runserver`

### Frontend Setup
1. Navigate to frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm start`
