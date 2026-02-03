.PHONY: default psql logs

default: psql

psql:
	docker compose exec -it -u postgres postgres psql -U postgres

logs:
	docker compose logs -f

sh: 
	docker compose exec postgres bash