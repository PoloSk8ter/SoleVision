from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_mail import Mail
db = SQLAlchemy()
DB_NAME = "database.db"

mail = Mail() 
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'


    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config["MAIL_USERNAME"]='junthefreakz@gmail.com'
    app.config['MAIL_PASSWORD']='wwrv yqoe rlwk cdha'  
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail.init_app(app) 

    db.init_app(app)

    from .auth import auth
    from .shoe_monitoring import shoe_monitoring
    from .stock_in import stock_in
    from .shoe_request import shoe_request
    from .cus_request import cus_request


    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(shoe_monitoring, url_prefix='/')
    app.register_blueprint(stock_in, url_prefix = '/')
    app.register_blueprint(shoe_request, url_prefix = '/')
    app.register_blueprint(cus_request, url_prefix = '/')


    from .models import User
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')