from models import User, Service, ServiceProfessional, ServiceRequest
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from flask_login import login_required
from database import db
from sqlalchemy import and_, func
from logger import logger


admin_views = Blueprint("admin_views",__name__, url_prefix='/admin')

@admin_views.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    users = User.query.all()
    services = Service.query.all()
    services_data = [service.serialize() for service in services]  
    
    sps = ServiceProfessional.query.all()
    srs = ServiceRequest.query.all()
    return render_template("admin_home.html", services=services_data, service_professionals=sps, srs=srs)

@admin_views.route("/summary", methods=["GET"])
@login_required
def admin_summary():
    ratings_data = (
        db.session.query(
            ServiceRequest.rating, func.count(ServiceRequest.id)
        )
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


    service_status_data = (
        db.session.query(
            ServiceRequest.service_status, func.count(ServiceRequest.id)
        )
        .group_by(ServiceRequest.service_status)
        .all()
    )

    bar_chart_data = [
        {"status": status, "count": count} for status, count in service_status_data
    ]

    
    return render_template("admin_summary.html", pie_chart_data=pie_chart_data, bar_chart_data=bar_chart_data)

@admin_views.route('/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory('../', filename)


@admin_views.route('/search', methods=['GET'])
@login_required
def search_service_requests():
    service_name = request.args.get('service_name', None)
    professional_name = request.args.get('professional_name', None)
    request_status = request.args.get('status', None)
    
    try:
        services = Service.query.all()
        query = ServiceRequest.query.join(Service, ServiceRequest.service_id == Service.id)\
                                    .outerjoin(ServiceProfessional, ServiceRequest.professional_id == ServiceProfessional.id)
        filters = []
        if service_name:
            filters.append(Service.name.ilike(f"%{service_name}%"))  
        if professional_name:
            filters.append(ServiceProfessional.fullname.ilike(f"%{professional_name}%")) 
        if request_status:
            filters.append(ServiceRequest.service_status == request_status)

        if filters:
            query = query.filter(and_(*filters))
        results = query.all()

        return render_template('admin_search.html', results=results,services=services)
    except Exception as e:
        logger.error('Error searching for service requests', str(e))
        return  render_template('admin_search.html', services=services)

@admin_views.route("/professional", methods=['DELETE', 'POST'])
@login_required
def delete_professional():
    if request.method == 'POST':
        professional_id = request.json['id']
        action = request.json['action']
        
        if action == 'approve':
            #updating status to Approved
            try:
                sp = ServiceProfessional.query.get_or_404(professional_id)
                sp.status = 'Approved'
                db.session.commit()
                return jsonify({'message': 'Service Professional approved successfully'}), 200
            except Exception as e:
                logger.error('Error approving service professional', str(e))
                db.session.rollback()
                return jsonify({'status': 500, 'message': 'Error approving service professional'}), 500
        elif action == 'reject':
            #updating status to Rejected
            try:
                sp = ServiceProfessional.query.get_or_404(professional_id)
                sp.status = 'Rejected'
                db.session.commit()
                return jsonify({'message': 'Service Professional rejected successfully'}), 200
            except Exception as e:
                logger.error('Error rejecting service professional', str(e))
                db.session.rollback()
                return jsonify({'status': 500, 'message': 'Error rejecting service professional'}), 500
    if request.method == 'DELETE':
        professional_id = request.json['id']
        try:
            sp = ServiceProfessional.query.get_or_404(professional_id)
            db.session.delete(sp)
            db.session.commit()
            return jsonify({'message': 'Service Professional deleted successfully'}), 200
        except Exception as e:
            logger.error('Error deleting service professional', str(e))
            db.session.rollback()
            return jsonify({'status': 500, 'message': 'Error deleting service professional'}), 500
    

@admin_views.route('/service', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_services():
    
    if request.method == 'POST':
        service_name = request.json['service_name']
        base_price = request.json['base_price']
        service_description = request.json['service_description']
        
        #creating new service
        try:
            new_service = Service(name=service_name, price=base_price, description=service_description)
            db.session.add(new_service)
            db.session.commit()
            return jsonify({'message': 'Service added successfully'}), 200
        except Exception as e:
            logger.error('Error creating new service', str(e))
            db.session.rollback()
            return jsonify({'status': 500, 'message': 'Error creating new service'}), 500
        
    elif request.method == 'PUT':
        service_id = request.json['id']
        service_name = request.json['service_name']
        base_price = request.json['base_price']
        service_description = request.json['service_description']
        
        #updating service
        try:
            
            service = Service.query.get_or_404(service_id)
            service.name = service_name
            service.price = base_price
            service.description = service_description
            db.session.commit()
            return jsonify({'message': 'Service updated successfully'}), 200
        except Exception as e:
            logger.error('Error updating service', str(e))
            db.session.rollback()
            return jsonify({'status': 500, 'message': 'Error updating service'}), 500
    elif request.method == 'DELETE':
        service_id = request.json['id']
        try:
            service = Service.query.get_or_404(service_id)
            db.session.delete(service)
            db.session.commit()
            return jsonify({'message': 'Service deleted successfully'}), 200
        except Exception as e:
            logger.error('Error deleting service', str(e))
            db.session.rollback()
            return jsonify({'status': 500, 'message': 'Error deleting service'}), 500
        
