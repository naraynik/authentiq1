# Shortcuts (Linux/macOS). On Windows use the commands in README.md.
.PHONY: up down logs ps test

up:      ## build and start the whole stack (needs .env)
	docker compose up -d --build

down:    ## stop the stack (data is kept in Docker volumes)
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test:    ## backend + website tests
	cd backend && python -m pytest -q tests
	cd frontend && bun run test
