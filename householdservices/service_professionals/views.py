from models import User, ServiceProfessional, Service, ServiceRequest, Customer
from flask import Blueprint, render_template, request, flash, redirect, jsonify
from flask_login import current_user, login_required

from database import db
from utils import create_hashed_password
from sqlalchemy import and_, func
from datetime import datetime, date
import uuid, os
from logger import logger



service_professional_views = Blueprint("service_professional_views",__name__, url_prefix='/serviceprofessionals')


@service_professional_views.route("/summary", methods=["GET"])
@login_required
def professional_summary():
    # getting the total number of service requests, service professionals, and users
    ratings_data = (
        db.session.query(
            ServiceRequest.rating, func.count(ServiceRequest.id)
        )
        .filter_by(professional_id=current_user.id) 
        .group_by(ServiceRequest.rating)
        .all()
    )

  
    total_count = sum(count for _, count in ratings_data)

    pie_chart_data = [
        {
            "rating": rating,
            "percentage": round((count / total_count) * 100, 2)  
        }
        for rating, count in ratings_data
    ]

    #bar chart summary
    service_status_data = (
        db.session.query(
            ServiceRequest.service_status, func.count(ServiceRequest.id)
        )
        .filter_by(professional_id=current_user.id) 
        .group_by(ServiceRequest.service_status)
        .all()
    )

    bar_chart_data = [
        {"status": status, "count": count} for status, count in service_status_data
    ]

    
    return render_template("admin_summary.html", pie_chart_data=pie_chart_data, bar_chart_data=bar_chart_data)

@service_professional_views.route("/search", methods=['GET'])
@login_required
def search_sps():
    date_of_completion = request.args.get('date_of_completion', None)
    location = request.args.get('location', None)
    pincode = request.args.get('pincode', None)
    professional_id = current_user.id  # Placeholder

    if not professional_id:
        flash("Unauthorized access", "danger")
        return render_template("professional_search.html")

 
    query = ServiceRequest.query.filter_by(professional_id=professional_id)

    filters = []
    if date_of_completion:
        try:
            filters.append(ServiceRequest.date_of_completion == datetime.strptime(date_of_completion, "%Y-%m-%d"))
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD", "info")
            return render_template("professional_search.html")
    if location:
        filters.append(Customer.address.ilike(f"%{location}%")) 
    if pincode:
        filters.append(Customer.pincode == pincode) 

    if filters:
        query = query.filter(and_(*filters))

    results = query.all()

    
    return render_template("professional_search.html", results=results)


@service_professional_views.route('/accept', methods=['POST'])
@login_required
def accept_request():


    if request.method == 'POST':
        sr_id = request.json.get('id')
        action = request.json.get('action')
        #update service_status in ServiceRequest to accepted
        try:
            service_request = ServiceRequest.query.get_or_404(sr_id)

            if action == 'accept':
                service_request.service_status = 'accepted'
            else:
                service_request.service_status = 'rejected'
            db.session.commit()
            db.session.refresh(service_request)
        except Exception as e:
            db.session.rollback()
            logger.error("Error when booking service", str(e))
            return jsonify({'status': 500, 'message': 'Error in accepting or rejecting service request '}), 500
        return jsonify({'message': 'Service '+action+' error'}), 200


def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf'}

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@service_professional_views.route('/dashboard')
@login_required
def sp_dashboard():
    #get all Service requests with todays data and status == requested
    today = date.today()
    service_requests_today = ServiceRequest.query.filter(
        db.func.date(ServiceRequest.date_of_request) == today,
    ).all()
    closed_service_requests = ServiceRequest.query.filter(
        db.func.date(ServiceRequest.date_of_request) == today,
        ServiceRequest.service_status == 'closed'
    ).all()



    return render_template('professional_home.html', service_requests_today=service_requests_today, closed_service_requests=closed_service_requests )



@service_professional_views.route('/signup',  methods=['POST', 'GET'])
def signup():
    services = Service.query.all()
    if request.method == 'POST':
        #create a new user
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists", "danger")
            return render_template("service_professional_signup.html")
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        service_name = request.form.get('service_name')
        experience = request.form.get('experience')
        try:
            if 'attachment' not in request.files:
                flash('Attachment not found', "info")
                return redirect(request.url)

            file = request.files['attachment']
            if file.filename == '':
                flash('No selected attachmet', "info")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                unique_filename = f"{uuid.uuid4().hex}.pdf" 
                file_path = os.path.join('uploads', unique_filename)
                file.save(file_path)
                hashed_password = create_hashed_password(password)
               
                
                #user added to user table, now add other details, serviceprofessional table
                service_professional = ServiceProfessional(
                    email=email, 
                    password=hashed_password, 
                    address=address, 
                    fullname=fullname, 
                    pincode=pincode,
                    user_type='serviceprofessional',
                    is_active=True,
                    is_blocked=False,
                    service_name = service_name,
                    experience = experience,
                    documents = unique_filename
                )
                db.session.add(service_professional)
                db.session.commit()
                logger.info("Service professional created!")
                flash("Registration successful. Please wait for admin approval", "success")
                return redirect('/')
            else:
                flash('Only PDF files are allowed', "info")
                return redirect(request.url)
            
        except Exception as e:
            print(f"Error occurred while creating user: {str(e)}")
            flash("Something went wrong", "danger")
            db.session.rollback()
            return render_template("service_professional_signup.html", services=services)
    return render_template("service_professional_signup.html", services=services)