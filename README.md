To enable psql command, add this into `.bashrc`:
```bash
alias psql='cd /path/to/this/directory && docker compose exec -it postgres psql -U postgres'
```