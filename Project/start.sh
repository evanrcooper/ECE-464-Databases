sudo mkdir -p /evanr
sudo touch /evanr/database.sqlite3
sudo chmod 777 /evanr/database.sqlite3

docker-compose build
docker-compose up