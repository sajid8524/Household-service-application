from datetime import datetime
from database import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin', 'customer', 'professional'
    is_blocked = db.Column(db.Boolean, default=False)
    fullname = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    pincode = db.Column(db.String(6), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


    customer_requests = db.relationship(
        'ServiceRequest', 
        foreign_keys='ServiceRequest.customer_id', 
        backref='customer', 
        lazy=True
    )

    __mapper_args__ = {
        'polymorphic_on': user_type,  # Specifies the column used for polymorphism
        'polymorphic_identity': 'user',  # Identifier for the User model
    }

    def __repr__(self):
        return f"<User {self.fullname}, Type: {self.user_type}>"


class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    requests = db.relationship('ServiceRequest', backref='service', lazy=True)

    def __repr__(self):
        return f"<Service {self.name}, Price: {self.price}>"

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
        }


class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)
    date_of_request = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(50), default="requested")
    rating = db.Column(db.Integer, nullable=False, default=3)
    remarks = db.Column(db.Text)

    def __repr__(self):
        return f"<ServiceRequest ID: {self.id}, Status: {self.service_status}>"
    def serialize(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "professional_id": self.professional_id,
            "date_of_request": self.date_of_request.isoformat() if self.date_of_request else None,
            "date_of_completion": self.date_of_completion.isoformat() if self.date_of_completion else None,
            "service_status": self.service_status,
            "rating": self.rating,
            "remarks": self.remarks,
        }

class ServiceProfessional(User):
    __tablename__ = 'service_professionals'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True) 
    service_name = db.Column(db.String, db.ForeignKey('services.name'), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    documents = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="Requested")
    service_requests = db.relationship(
        'ServiceRequest', 
        foreign_keys='ServiceRequest.professional_id', 
        backref='professional', 
        lazy=True
    )

    __mapper_args__ = {
        'polymorphic_identity': 'serviceprofessional',  
    }

    def serialize(self):
        return {
            "id": self.id,
            "fullname": self.fullname,
            "address": self.address,
            "service_name": self.service_name,
            "experience": self.experience,
            "documents": self.documents,
            "service_requests": [request.serialize() for request in self.service_requests]
        }

    def __repr__(self):
        return f"<ServiceProfessional ID: {self.id}, Service: {self.service_name}>"
    
    
class Admin(User):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': 'admin',  # Identity for 'admin'
    }

class Customer(User):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': 'customer',  # Identity for 'customer'
    }
    
