from flask import render_template, request, current_app, redirect, url_for
from flask_login import login_required, current_user
from app.api.external_service import get_property_data
from app.api.blackknight_service import get_blackknight_data
from app.models import APIRequest, db
import json
from app.api.housecanary_service import get_housecanary_data

def init_app(app):
    @app.route('/', methods=['GET', 'POST'])
    @login_required
    def index():
        # Fetch request history
        requests = APIRequest.query.filter_by(user_id=current_user.id).order_by(APIRequest.timestamp.desc()).all()

        if request.method == 'POST':
            api_provider = request.form.get('api_provider')
            address = request.form.get('address')
            city = request.form.get('city')
            state = request.form.get('state')
            zip_code = request.form.get('zip')
            apn = request.form.get('apn')
            fips = request.form.get('fips')

            try:
                if api_provider == 'batchdata':
                    result = get_property_data(address, city, state, zip_code, apn, fips)
                elif api_provider == 'blackknight':
                    result = get_blackknight_data(address, city, state, zip_code, apn, fips)
                elif api_provider == 'housecanary':
                    result = get_housecanary_data(address, city, state, zip_code, apn, fips)
                else:
                    raise ValueError(f"Invalid API provider selected: {api_provider}")
            except Exception as e:
                current_app.logger.error(f"An error occurred: {str(e)}")
                error_message = str(e)
                if "Authentication failed" in error_message:
                    error_message += " Please check your API credentials in the configuration file."
                return render_template('index.html', error=error_message, requests=requests)

            # Save the request to the database
            api_request = APIRequest(
                user_id=current_user.id,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                apn=apn,
                fips=fips,
                service=api_provider,
                response_data=json.dumps(result)
            )
            db.session.add(api_request)
            db.session.commit()

            # Redirect to the view_request page
            return redirect(url_for('view_request', request_id=api_request.id))

        # Pass the requests to the template
        return render_template('index.html', requests=requests)

    @app.route('/request/<int:request_id>')
    @login_required
    def view_request(request_id):
        api_request = APIRequest.query.get_or_404(request_id)
        if api_request.user_id != current_user.id:
            return redirect(url_for('index'))
        response_data = json.loads(api_request.response_data)
        return render_template('view_request.html', request=api_request, response_data=response_data)