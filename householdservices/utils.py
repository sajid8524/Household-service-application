from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User


def create_hashed_password(password):
    # Generate a hashed password
    hashed_password = generate_password_hash(password)
    return hashed_password



# Verifying a password during login
def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

def pre_populate_admin_user(username, password,email):
    
    admin_user = User.query.filter(User.email == "admin@gmail.com").first()
    if not admin_user:
        admin_user = User(password=create_hashed_password(password), user_type='admin', email=email, is_active=True, fullname='ADMIN')
        db.session.add(admin_user)
        db.session.commit()


