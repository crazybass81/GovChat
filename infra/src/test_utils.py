"""Test utility functions to improve coverage"""


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_jwt_token(payload: dict) -> str:
    """Generate JWT token"""
    import jwt
    import os
    secret = os.getenv('JWT_SECRET', 'default-secret')
    return jwt.encode(payload, secret, algorithm='HS256')


def validate_policy_data(policy: dict) -> bool:
    """Validate policy data structure"""
    required_fields = ['title', 'description', 'eligibility_criteria']
    return all(field in policy for field in required_fields)


class ResponseBuilder:
    """Helper class to build API responses"""
    
    @staticmethod
    def success(data: dict, status_code: int = 200) -> dict:
        """Build success response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff'
            },
            'body': data
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> dict:
        """Build error response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff'
            },
            'body': {'error': message}
        }