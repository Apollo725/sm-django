while getopts m: option
do
 case "${option}"
 in
 m) mode=${OPTARG};;
 esac
done

rm -rf .env
if [ "$mode" == "on" ]
then
    echo "TEST_MODE=on" >> .env
else
    echo "TEST_MODE=off" >> .env
fi

docker-compose down
docker-compose run -d -p 8080:80 runtime python manage.py runserver 0.0.0.0:80
docker-compose run -d runtime python manage.py mocks