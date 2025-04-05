from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from extentions import db
from datetime import datetime

def create_data(user_datastore: SQLAlchemyUserDatastore):
    print('### creating Data #######')

    user_datastore.find_or_create_role(name='admin', description="Administrator")
    user_datastore.find_or_create_role(name='prof', description="Professional")
    user_datastore.find_or_create_role(name='cust', description="Customer")


    if not user_datastore.find_user(email="admin@gmail.com"):
        user_datastore.create_user(
            email="admin@gmail.com",
            password=hash_password('admin1234'),
            active=True,
            roles=['admin'],
            full_name="Admin User",  
            mobile="0000000000",     
            location="City",   
            pincode="9999999",       
            date_created=datetime.utcnow()
                
        )

    db.session.commit()