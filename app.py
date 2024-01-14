from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
# Zmieniony import dla wyjątków SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///store.db')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name} x {self.price}>'


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    def __repr__(self):
        return f'<CartItem User: {self.user_id} Product: {self.product_id} Quantity: {self.quantity}>'


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        return None


@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'message': 'Logged in successfully'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/current_user', methods=['GET'])
@login_required
def get_current_user():
    try:
        return jsonify({'username': current_user.username}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/products', methods=['GET'])
def list_products():
    try:
        products = Product.query.all()
        return jsonify([{'id': product.id, 'name': product.name, 'price': product.price} for product in products])
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        new_product = Product(name=data['name'], price=data['price'])
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully',
                        'product': {'id': new_product.id,
                                    'name': new_product.name,
                                    'price': new_product.price
                                    }}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify({'id': product.id, 'name': product.name, 'price': product.price})
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/cart', methods=['GET'])
@login_required
def get_cart_items():
    try:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_items_data = [{
            'id': item.id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'name': item.product.name,
            'price': item.product.price
        } for item in cart_items]
        return jsonify(cart_items_data)
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        cart_item = CartItem.query.filter_by(
            user_id=current_user.id, product_id=product_id).first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id,
                                 product_id=product_id, quantity=quantity)

        db.session.add(cart_item)
        db.session.commit()

        return jsonify({'message': 'Product added to cart',
                        'cartItem': {'product_id': cart_item.product_id,
                                     'quantity': cart_item.quantity
                                     }}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error occurred'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
