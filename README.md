in flask/
flask db init
flask db migrate -m "opis zmiany"
flask db upgrade

in vue/
npm install
npm run serve

python -m pytest

python app.py

docker build -t flaskcandyshop .
docker run -d --name flaskcandyshop -p 5000:5000 flaskcandyshop
