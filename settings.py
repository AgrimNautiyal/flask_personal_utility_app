from os import environ
SECRET_KEY = environ.get('SECRET_KEY')
SENDGRID_API_KEY = environ.get('SENDGRID_API_KEY')
FROM_EMAIL = environ.get('FROM_EMAIL')
TO_EMAILS = environ.get('TO_EMAILS')
