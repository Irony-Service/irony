# Pull latest code, rebuild, and restart containers
update:
	git pull
	docker-compose down
	docker-compose up --build -d

# Restart containers without rebuilding
restart:
	docker-compose restart

# View logs in real-time
logs:
	docker-compose logs -f

# Stop all containers without removing them
stop:
	docker-compose stop

# Remove all containers, networks, and volumes (use with caution!)
clean:
	docker-compose down -v

# Rebuild and restart only the backend
backend-rebuild:
	docker-compose stop irony_backend
	docker-compose build irony_backend
	docker-compose up -d irony_backend

# Rebuild and restart only the frontend
frontend-rebuild:
	docker-compose stop irony_frontend
	docker-compose build irony_frontend
	docker-compose up -d irony_frontend

# Open an interactive shell inside the backend container
backend-shell:
	docker exec -it irony_backend bash

# Open an interactive shell inside the frontend container
frontend-shell:
	docker exec -it irony_frontend bash

# Run database migrations (modify this based on your migration tool)
migrate:
	docker exec -it irony_backend alembic upgrade head

# Show running containers
ps:
	docker-compose ps

# Remove all unused Docker images and containers (useful for freeing space)
prune:
	docker system prune -af
