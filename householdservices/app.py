from flask import Flask, render_template, request, redirect, flash, send_from_directory
from database  import db
from customer.views import customer_views
from admin.views import admin_views
from service_professionals.views import service_professional_views
from utils import pre_populate_admin_user
from flask_login import LoginManager, login_required, login_user, logout_user
from utils import create_hashed_password
from werkzeug.security import  check_password_hash


from models import User
import os

login_manager = LoginManager()

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///housedhold.db'
    app.secret_key = 'SqKuMnnEpXzRPKJzojMAYpEjRcpaFYgVOVwiSFOtoEBDQnjrukMjupzDcwURQHjkQcrgLHkcacGNHBFtpTcUWiBSSfNRejxoXgMn'

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(customer_views)
    app.register_blueprint(admin_views)
    app.register_blueprint(service_professional_views)
    with app.app_context():
        db.create_all()
        pre_populate_admin_user("admin", "admin123A", "admin@gmail.com")
    return app


app = create_app()


UPLOAD_FOLDER = './uploads'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_blocked:
                flash("Your account is blocked. Please contact the admin.", "danger")
                return redirect("/")
            if user.user_type != "serviceprofessional":
                login_user(user)  
                redirect_url = '/'
                if user.user_type == "admin":
                    redirect_url = "/admin/dashboard"
                elif user.user_type == "customer":
                    redirect_url = "/customer/dashboard"
            else:
                if user.status == "Approved":
                    login_user(user)
                    redirect_url = "/serviceprofessionals/dashboard"
                elif user.status == 'Rejected':
                    flash("Admin rejected your service", "danger")
                    return redirect("/")
                else:
                    flash("Your account is pending for approval. Please wait for admin approval.", "danger")
                    return redirect("/")
                
            return redirect(redirect_url)
        else:
            flash("Invalid email or password.", "danger")

            return render_template("login.html")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return "Welcome to the protected dashboard!"



@app.route("/logout")
@login_required
def logout():
    logout_user()  
    return redirect("/")


if __name__ == "__main__":
    
    app.run(debug=True)
    