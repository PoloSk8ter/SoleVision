from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import base64
from . import mail
from flask_mail import Message
from random import randint

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET'])
@login_required
def home():
    role = current_user.role 
    if role == "admin":
        with open('homeimage1.JPG', 'rb') as img_file:
            image_data = img_file.read()
            home1 = base64.b64encode(image_data).decode('utf-8')
        with open('homeimage2.JPG', 'rb') as img_file:
            image_data = img_file.read()
            home2 = base64.b64encode(image_data).decode('utf-8')
        with open('brandlogo.png', 'rb') as img_file:
            image_data = img_file.read()
            logo = base64.b64encode(image_data).decode('utf-8')
        return render_template("home.html", home1= home1, home2= home2, logo = logo, user=current_user)
    else:
        return redirect(url_for('shoe_request.cushome'))
    
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('auth.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    with open('loginimage1.JPG', 'rb') as img_file:
        image_data = img_file.read()
        nike = base64.b64encode(image_data).decode('utf-8')
    with open('loginimage2.JPG', 'rb') as img_file:
        image_data = img_file.read()
        adidas = base64.b64encode(image_data).decode('utf-8')
    
    return render_template("login.html", nike = nike, adidas = adidas, user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash( password1, method='pbkdf2:sha256'), role ="customer")
            db.session.add(new_user)
            db.session.commit()
            role = new_user.role
            if role =="admin":
                login_user(new_user, remember=True)
                flash('Account created! WELCOME', category='success')
                return redirect(url_for('auth.home'))
            else:
                login_user(new_user, remember=True)
                flash('Account created! WELCOME', category='success')
                return redirect(url_for('shoe_request.cushome'))
            

    with open('loginimage1.JPG', 'rb') as img_file:
        image_data = img_file.read()
        nike = base64.b64encode(image_data).decode('utf-8')
    with open('loginimage2.JPG', 'rb') as img_file:
        image_data = img_file.read()
        adidas = base64.b64encode(image_data).decode('utf-8')
    return render_template("sign_up.html", nike = nike, adidas = adidas, user=current_user)


@auth.route('/profile', methods=['GET', 'POST'])
def change_password():
    email = current_user.email
    name = current_user.first_name
    if request.method == 'POST':
        old = request.form.get('old')
        new = request.form.get('new')
        confirm = request.form.get('confirm')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, old):
                if old != new:
                    if new != confirm:
                        flash('New and confirm passwords do not match.', category='error')
                    else:
                        hashed_new_password = generate_password_hash(new, method='pbkdf2:sha256')
                        user.password = hashed_new_password
                        # Save the changes to the database
                        db.session.commit()

                        flash('Password updated successfully!', category='success')
                else:
                    flash('Old password and New Password Cant be Same, try again.', category='error')             
            else:
                flash('Incorrect old password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')


    return render_template("profile.html", name=name , email=email, user=current_user)



otp=randint(000000,999999)

@auth.route('/sendemail',methods=["GET","POST"])
def send_email():
    email=request.form.get('email') 
    user = User.query.filter_by(email=email).first()
    if user:
        msg=Message(subject='SoleVision Validation Email',sender='junthefreakz@gmail.com',recipients=[email])
        charotp = str(otp)
        msg.body=  f'Your OTP for SoleVision email validation is: {charotp }. Please use it within 5 minutes.'
        mail.send(msg)
        return jsonify({'success': True})

    else:
        return jsonify({'success': False})

    

@auth.route('/validate',methods=['GET','POST'])
def validate():
    if request.method =="POST":
        valemail=request.form.get('email') 
        user_otp=request.form.get('otp')
        if otp==int(user_otp):
            user = User.query.filter_by(email=valemail).first()
            email = user.email
            name = user.first_name
            flash('VALIDATE SUCCESSFULLY! PLEASE CHANGE YOUR PASSWORD', category='success')
            return render_template("forgot_password.html", name=name , email=email, user=current_user)
        else:
            flash('OTP DOES NOT MATCH PLEASE TRY AGAIN', category='error')
    return render_template("validation.html",user = current_user)


@auth.route('/update_new', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':
        email = request.form.get('hidden_email')
        name = request.form.get('hidden_name')
        new = request.form.get('new')
        confirm = request.form.get('confirm')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, new):
                flash('New Password Should not be same as Old Password', category='error')   
            else:

                if new != confirm:
                    flash('New and confirm passwords do not match.', category='error')
                else:
                    hashed_new_password = generate_password_hash(new, method='pbkdf2:sha256')
                    user.password = hashed_new_password
                    # Save the changes to the database
                    db.session.commit()

                    flash('Password updated successfully!', category='success')
                    return redirect(url_for('auth.login'))           
        else:
            flash('Email does not exist.', category='error')

    return render_template("forgot_password.html", name=name , email=email, user=current_user)
