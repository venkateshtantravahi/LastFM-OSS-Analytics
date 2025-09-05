.PHONY: up down logs fmt lint test
up:
	cd infra && docker compose --env-file .env up -d

down:
	cd infra && docker compose --env-file .env down -v

logs:
	cd infra && docker compose logs -f --tail=200

fmt:
	pre-commit run -a

test:
	pytest -q
