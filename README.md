# Django Real-Time Chat System

A real-time chat application built with Django and Django Channels, enabling instant messaging between users.

## Features

- **User Authentication**: Custom user model tracking online status and last seen timestamps.
- **Real-Time Messaging**: WebSocket integration using Django Channels for instant message delivery.
- **Message History**: Persistent storage of chat history between users using SQLite.
- **Read Receipts**: Tracking whether a message has been read or not.
- **delete message**: delete message from the chat.
- **Unread message count**: show unread message count in the chat list.
- **online status**: show online status of users.
- **last seen**: show last seen time of users.

## Tech Stack

- **Backend**: Python, Django 5.2
- **WebSockets**: Django Channels 4.3, Daphne, In-Memory Channel Layer (development configuration)
- **Database**: SQLite3
- **Frontend**: Django Templates, HTML/CSS/JavaScript

## Project Structure

- `chat_system/`: Main Django project configuration and settings, URL routing, and basic structure.
- `chat_app/`: Core chat application containing models, views, and consumers for routing WebSocket connections.
- `templates/`: HTML templates for the frontend (e.g., login, register, chat interface).

## Setup Instructions

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd <repository>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. **Install dependencies**:
   Ensure you are in the directory containing `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Navigate to the main directory**:
   ```bash
   cd chat_system
   ```

5. **Run database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```
   *Note: Since this project uses Django Channels and Daphne is installed, `runserver` will automatically route WebSocket/HTTP traffic.*

7. **Access the application**:
   Open a browser and navigate to `http://127.0.0.1:8000/`. You may be redirected to the configured login/register URLs.

8. **Test the application**:
   - Open two browser windows and log in with different users.
   - 
