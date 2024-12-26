from models import User,  ServiceProfessional, Service, ServiceRequest, Customer
from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import current_user, login_required
from utils import create_hashed_password
from sqlalchemy import and_, func
from logger import logger
from database import db
import datetime

customer_views = Blueprint("customer_views",__name__, url_prefix='/customer')


@customer_views.route('/summary', methods=['GET'])
@login_required
def customer_summary():
    customer_data = (
        db.session.query(
            ServiceRequest.service_status, func.count(ServiceRequest.id)
        )
        .filter_by(customer_id=current_user.id)
        .group_by(ServiceRequest.service_status)
        .all()
    )

    bar_chart_data = [
        {"status": status, "count": count} for status, count in customer_data
    ]

    return render_template("customer_summary.html",  bar_chart_data=bar_chart_data)


@customer_views.route("/search", methods=['GET'])
@login_required
def search_customers():
    try:
        services = Service.query.all()

        professional_name = request.args.get('professional_name', None)
        service_name = request.args.get('service_name', None)
        location = request.args.get('location', None)  

        query = ServiceProfessional.query.join(Service, ServiceProfessional.service_name == Service.name)

        # adding filters
        filters = []
        if professional_name:
            filters.append(ServiceProfessional.fullname.ilike(f"%{professional_name}%")) 
        if service_name:
            filters.append(Service.name.ilike(f"%{service_name}%")) 
        if location:
            filters.append(ServiceProfessional.address.ilike(f"%{location}%")) 

        if filters:
            query = query.filter(and_(*filters))

        results = query.all()
        
        return render_template("customer_search.html", results=results, services=services)
    except Exception as e:
        logger.error('Error searching for service requests', str(e))
        return  render_template('customer_search.html', services=services)
    
@customer_views.route('/close', methods=['POST'])
@login_required
def accept_request():


    if request.method == 'POST':
        sr_id = request.json.get('id')
        #update service_status in ServiceRequest to closed
        try:
            service_request = ServiceRequest.query.get_or_404(sr_id)
            service_request.service_status = 'closed'
            service_request.date_of_completion = datetime.datetime.now()
            db.session.commit()
            db.session.refresh(service_request)
        except Exception as e:
            db.session.rollback()
            logger.error("Error when booking service", str(e))
            return jsonify({'status': 500, 'message': 'Error in accepting or rejecting service request '}), 500
        return jsonify({'message': 'Service closing error'}), 200

@customer_views.route('/rating', methods=['POST'])
@login_required
def rate_request():


    if request.method == 'POST':
        sr_id = request.json.get('id')
        rating = request.json.get('rating')
        #update service_status in ServiceRequest to closed
        try:
            service_request = ServiceRequest.query.get_or_404(sr_id)
            service_request.rating = int(rating)
            db.session.commit()
            db.session.refresh(service_request)
        except Exception as e:
            db.session.rollback()
            logger.error("Error when updating rating", str(e))
            return jsonify({'status': 500, 'message': 'Error when giving rating to service request '}), 500
        return jsonify({'message': 'Service rating error'}), 200


@customer_views.route('/dashboard')
@login_required
def customer_dashboard():
    sps = ServiceProfessional.query.all()
    services = Service.query.all()
    customer =  User.query.get_or_404(current_user.id),
    service_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()
    data = []
    for sr in service_requests:
        data.append({
            "id": sr.id,
            "service_name": sr.service.name,
            "professional_name": sr.professional.fullname,
            "status": sr.service_status,
        })
    return render_template('customer_home.html', sps=sps, services=services, customer=customer, srs=service_requests)

@customer_views.route("/book", methods=['POST'])
@login_required
def book_service():
    professional_id = request.json['professional_id']
    sp = ServiceProfessional.query.get_or_404(professional_id)
    service = Service.query.filter_by(name=sp.service_name).first()
    try:
        service_request = ServiceRequest(
            customer_id=current_user.id,
            service_id=service.id,
            professional_id=professional_id
        )
        db.session.add(service_request)
        db.session.commit()
        db.session.refresh(service_request)
        
        data = {
            "id": service_request.id,
            "service_name": sp.service_name,
            "fullname": sp.fullname,
            "status": service_request.service_status
        }
    except Exception as e:
        db.session.rollback()
        logger.error("Error when booking service", str(e))
        return jsonify({'status': 500, 'message': 'Error booking service '}), 500
    return jsonify({'message': 'Service Booked', 'data': data}), 200

@customer_views.route("/professional", methods=['GET', 'POST'])
@login_required
def get_service_professionals():
    
    if request.method == 'POST':
        service_id = request.json['id']
        service = Service.query.get_or_404(service_id)
        
        # fetching Service Professionals related to the service
        service_professionals = ServiceProfessional.query.filter(
            ServiceProfessional.service_name == service.name,
            ServiceProfessional.status=="Approved"
        ).all()

        # calculating average rating for each professional
        professionals_with_ratings = []
        for sp in service_professionals:
            # Fetch all service requests for the professional
            service_requests = ServiceRequest.query.filter_by(professional_id=sp.id).all()

            # Extract ratings for the service requests
            ratings=  []
            
            for ser_request in service_requests:
                ratings.append(int(ser_request.rating))
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            data = sp.serialize()
            data['rating'] = avg_rating
            data['price'] = service.price
            keys_to_remove = ["experience", "documents", "service_requests"]

            for key in keys_to_remove:
                data.pop(key, None)
            professionals_with_ratings.append(data)
        return  {'professionals': professionals_with_ratings}


@customer_views.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        #create a new user
        email = request.form.get('email')
        
        #check user already exists with this email or not
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists", "danger")
            return render_template("customer_signup.html")
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        try:
            hashed_password = create_hashed_password(password)
            new_user = User(
                email=email, 
                password=hashed_password, 
                address=address, 
                fullname=fullname, 
                pincode=pincode,
                user_type='customer',
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful", "success")
        except Exception as e:
            print(f"Error occurred while creating user: {str(e)}")
            flash("Something went wrong", "danger")

        return render_template("login.html")

    return render_template("customer_signup.html")