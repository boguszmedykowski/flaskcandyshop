import pytest
from app import app, db, Product


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.drop_all()


def test_list_products(client):
    """Test the /products route."""
    response = client.get('/products')
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_get_product(client):
    """Test the /product/<int:product_id> route."""
    with app.app_context():
        product = Product(name='Test Product', price=9.99)
        db.session.add(product)
        db.session.commit()

        product_id = product.id

    response = client.get(f'/product/{product_id}')
    assert response.status_code == 200
    assert response.json['name'] == 'Test Product'


def test_get_product_requery(client):
    """Test the /product/<int:product_id> route with requerying."""
    with app.app_context():
        product = Product(name='Test Product', price=9.99)
        db.session.add(product)
        db.session.commit()

        product_id = product.id
        product = db.session.get(Product, product_id)

    response = client.get(f'/product/{product_id}')
    assert response.status_code == 200
    assert response.json['name'] == 'Test Product'


def test_add_to_cart(client):
    """Test the /add_to_cart/<int:product_id> route."""
    with app.app_context():
        product = Product(name='Test Product', price=9.99)
        db.session.add(product)
        db.session.commit()

        product_id = product.id
        product = db.session.get(Product, product_id)

    response = client.post(f'/add_to_cart/{product_id}')
    assert response.status_code == 200
    assert 'Produkt dodany do koszyka' in response.json['message']
