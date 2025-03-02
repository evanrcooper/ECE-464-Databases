sudo mkdir -p /evanr
sudo touch /evanr/database.sqlite3
sudo chmod 777 /evanr/database.sqlite3

sudo mkdir -p /evanr/articles
sudo chmod 777 /evanr/articles

sudo mkdir -p /evanr/summaries
sudo chmod 777 /evanr/summaries

docker-compose build
docker-compose up