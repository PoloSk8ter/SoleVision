from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import current_user
from . import db
from .models import Request,Model,Brand

cus_request = Blueprint('cus_request', __name__)



@cus_request.route('/personal-request')
def personal_request():
    pending_requests = Request.query.filter_by(user_id= current_user.id).all()
    for request in pending_requests:
        # Calculate the time difference in minutes
        brand = Brand.query.filter_by(id=request.brand_id).first()
        model = Model.query.filter_by(id=request.model_id).first()
        request.brand_name = brand.brand
        request.model_name = model.model_name
    return render_template('cus_request.html', requests=pending_requests, user=current_user)


@cus_request.route('/close-request',methods=['POST'])
def close_request():
    request_id = request.form['request_id']
    # Fetch the request by ID and update its status to 'accepted' in the database
    customer_request = Request.query.get(request_id)
    customer_request.status = 'CLOSED'
    db.session.commit()

    flash('REQUEST CLOSED', category='success')
    return redirect(url_for('cus_request.personal_request'))


@cus_request.route('/received-request',methods=['POST'])
def received_request():
    request_id = request.form['request_id']
    # Fetch the request by ID and update its status to 'accepted' in the database
    customer_request = Request.query.get(request_id)
    customer_request.status = 'RECEIVED'
    db.session.commit()

    flash('SHOE RECEIVED FROM STAFF', category='success')
    return redirect(url_for('cus_request.personal_request'))

# @cus_request.route('/edit-request')
# def personal_request():