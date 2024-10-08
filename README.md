
# Flask App with User Auth

A starter project for Flask applications with user authentication.

## Features

- User registration
- User login and logout
- Password reset via email
- SQLAlchemy database integration
- Flask-Mail for email sending
- Environment-based configuration
- Blueprints for modular app structure

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flask-auth-starter.git
   cd flask-auth-starter
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy the `.env.sample` file to `.env` and update the values:
     ```bash
     cp .env.sample .env
     ```
   - Edit the `.env` file with your specific configuration.

5. **Set up the database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   flask run
   ```
   The app should now be running at [http://localhost:5000](http://localhost:5000).

## Configuration

The app uses a `Config` class in `config.py` to manage configuration settings. Environment-specific settings are loaded from the `.env` file.

### Email Configuration (Mailtrap)

This app uses Mailtrap for email testing. To set up Mailtrap:

1. Sign up for a free account at [Mailtrap](https://mailtrap.io/)
2. Go to your Mailtrap inbox
   - Click on "Show Credentials" under "SMTP Settings"
3. Update your `.env` file with the Mailtrap credentials:
   ```bash
   MAIL_SERVER=smtp.mailtrap.io
   MAIL_PORT=2525
   MAIL_USERNAME=your_mailtrap_username
   MAIL_PASSWORD=your_mailtrap_password
   MAIL_USE_TLS=True
   MAIL_DEFAULT_SENDER=noreply@example.com
   ```

## Using Blueprints

This app uses Flask blueprints to organize routes and views. The authentication-related routes are in the `auth` blueprint.

### To create a new blueprint:

1. Create a new directory in the `app` folder (e.g., `app/new_feature`)
2. Create an `__init__.py` file in the new directory:
   ```python
   from flask import Blueprint
   bp = Blueprint('new_feature', name)
   from app.new_feature import routes
   ```
3. Create a `routes.py` file in the new directory and define your routes.
4. Register the blueprint in `app/__init__.py`:
   ```python
   from app.new_feature import bp as new_feature_bp
   app.register_blueprint(new_feature_bp)
   ```

## Development Tips

1. Use `flask shell` to interact with your app's context and test database queries.
2. Enable debug mode by setting `FLASK_ENV=development` in your `.env` file.
3. Use Flask-Migrate to manage database schema changes:
   ```bash
   flask db migrate -m "Description of changes"
   flask db upgrade
   ```
4. Customize the HTML templates in the `app/templates` directory.
5. Add custom CSS and JavaScript in the `app/static` directory.
6. Implement form validation using Flask-WTF for more robust user input handling.
7. Consider adding Flask-Login for more advanced user session management.

## Deployment

For production deployment:

1. Use a production-grade WSGI server like Gunicorn.
2. Set up a reverse proxy with Nginx.
3. Use a production database like PostgreSQL.
4. Configure a proper email service (e.g., SendGrid, Amazon SES).
5. Set `FLASK_ENV=production` and ensure `DEBUG=False`.
6. Use a secret key manager for sensitive information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
