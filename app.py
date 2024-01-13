from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import request
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name} x {self.price}>'


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey(
        'product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    product = db.relationship(
        'Product', backref=db.backref('cart_items', lazy=True))

    def __repr__(self):
        return f'<CartItem {self.product.name} x {self.quantity}>'


@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    return jsonify([{'id': product.id, 'name': product.name, 'price': product.price} for product in products])


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        new_product = Product(name=data['name'], price=data['price'])
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully', 'product': {'id': new_product.id, 'name': new_product.name, 'price': new_product.price}}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price})


@app.route('/cart', methods=['GET'])
def get_cart_items():
    cart_items = CartItem.query.all()
    cart_items_data = [{
        'id': item.id,
        'product_id': item.product_id,
        'quantity': item.quantity,
        'name': item.product.name,
        'price': item.product.price
    } for item in cart_items]
    return jsonify(cart_items_data)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        cart_item = CartItem(product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
        db.session.commit()

        return jsonify({'message': 'Product added to cart', 'cartItem': {'product_id': cart_item.product_id, 'quantity': cart_item.quantity}}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
