# Flask Authentication App

This is a Flask application that demonstrates user authentication, including signup, login, password reset, and an admin view.

## Features

- User signup and login
- Password reset functionality
- Admin view to list all users
- Basic error handling (404 and 500 errors)

## Prerequisites

- Python 3.7+
- pip
- virtualenv (optional but recommended)

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-auth-app
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your `.env` file:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file and fill in your specific details (secret key, mail settings, etc.)

5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the application:
   ```
   flask run
   ```

The application should now be running at `http://localhost:5000`.

## Usage

- Visit `/` to access the home page (requires login)
- Visit `/signup` to create a new account
- Visit `/login` to log in to an existing account
- Visit `/admin` to view all users (requires admin privileges)

## Project Structure

```
flask-auth-app/
├── app.py
├── models.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── templates/
    ├── base.html
    ├── home.html
    ├── signup.html
    ├── login.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── admin.html
    ├── 404.html
    └── 500.html
```

## Contributing

Please feel free to submit issues and pull requests.

## License

This project is open source and available under the [MIT License](LICENSE).