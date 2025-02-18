docker rm evanr_postgres || true

docker compose build

docker compose up -d

docker exec -it evanr_postgres psql -U evanr -d evanrdb