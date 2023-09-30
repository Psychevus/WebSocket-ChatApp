# Real-Time Chat Application


## Overview

This is a real-time chat application built using Python, Django, and Redis. It allows users to send and receive messages in real-time, utilizing WebSockets for instant communication. The application is designed with a focus on scalability, performance, and security.

## Features

- Real-time messaging with WebSocket support.
- User authentication with MySQL database.
- API throttling for message delivery.
- Proper error handling and form validation.
- Logging and monitoring for tracking application performance.
- Detailed testing for ensuring application reliability.

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x
- Django
- Redis
- MySQL
- Docker (for local development)

### Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/Psychevus/WebSocket-ChatApp.git
   cd WebSocket-ChatApp
   ```

2. Create a virtual environment and activate it:

   ```shell
   python -m venv venv
   source venv/bin/activate
   ```

3. Install project dependencies:

   ```shell
   pip install -r requirements.txt
   ```

4. Configure environment variables by copying the `.env.example` file to `.env` and customizing it:

   ```shell
   cp .env.example .env
   ```

5. Apply database migrations:

   ```shell
   python manage.py migrate
   ```

6. Start the development server:

   ```shell
   python manage.py runserver
   ```

7. Access the application in your browser at `http://localhost:8000`.

## Usage

- Visit the application in your browser.
- Sign up for an account using your name, last name, and email.
- Log in to access your conversations or start a new one.
- Enjoy real-time chat with other users.

## Testing

To run tests, use the following command:

```shell
python manage.py test
```

## Deployment

To deploy the application, follow these steps:

1. Configure deployment settings in your chosen cloud platform.
2. Set environment variables as specified in the `.env.example` file.
3. Deploy the application according to your chosen platform's instructions.

## API Throttling

API calls for message delivery are throttled to ensure smooth operation. Throttling rules can be customized in the application settings.

## Logging and Monitoring

The application includes comprehensive logging and monitoring to track API calls and application performance. Logs are stored according to the specified format in the application settings.

## Contributing

Contributions are welcome! Please follow these guidelines:

- Fork the repository.
- Create a new branch.
- Make your changes.
- Test your changes.
- Create a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
