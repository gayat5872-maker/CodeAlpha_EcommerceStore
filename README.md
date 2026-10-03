# CodeAlpha Django E-commerce

## Features
- Product listing and search
- Product detail page
- Session-based shopping cart
- User registration/login/logout
- Checkout and order processing
- SQLite database for users, products and orders
- Django admin for product/order management
- Stock tracking

## Run locally

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and use /admin/ to add products.

## Notes
This is a starter/demo store. For production, configure a secure SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, HTTPS, payment gateway, email, and stronger password/security settings.
