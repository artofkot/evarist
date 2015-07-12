from itsdangerous import URLSafeTimedSerializer

import evarist


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(evarist.app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=evarist.app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(evarist.app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=evarist.app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email