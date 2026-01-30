.PHONY: default psql logs

default: psql

psql:
	docker compose exec -it postgres psql -U postgres

logs:
	docker compose logs -f