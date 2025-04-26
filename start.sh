docker compose down -v
docker compose up -d --build

echo "Waiting for containers to start (5 seconds)..."
sleep 5

docker exec -it $(docker ps -qf "name=backend") python load_data.py
echo "Setup complete!" 