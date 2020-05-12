rm -rf .env
echo "TEST_MODE=on" >> .env
docker-compose down
docker-compose up -d
docker-compose run -d -p 8080:80 runtime python manage.py runserver 0.0.0.0:80
docker-compose run -d runtime python manage.py mocks