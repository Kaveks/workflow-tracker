# Makefile Guide

All commands are run from the **project root** (`workflow-tracker/`) where the
`Makefile` lives.

```sh
make <target>
```

Running `make` with no target prints the help table (the first target in the file).

---

## Quick reference

| Command                 | What it does                                           |
| ----------------------- | ------------------------------------------------------ |
| `make` / `make help`    | Print all available targets with descriptions          |
| `make build`            | Build Docker images for backend and frontend           |
| `make up`               | Start the full stack in the background                 |
| `make down`             | Stop and remove containers (volume kept)               |
| `make logs`             | Stream live logs from all services                     |
| `make restart`          | Stop then start the stack                              |
| `make clean`            | Full tear-down — containers, volumes, and local images |
| `make test`             | Run backend tests inside the running container         |
| `make migrate`          | Apply Django migrations inside the running container   |
| `make createsuperuser`  | Create a Django admin superuser interactively          |
| `make backend-shell`    | Open an interactive shell in the backend container     |
| `make backend-install`  | Install Python dependencies locally (no Docker)        |
| `make frontend-install` | Install Node dependencies locally (no Docker)          |
| `make dev-backend`      | Run the Django dev server locally (no Docker)          |
| `make dev-frontend`     | Run the Next.js dev server locally (no Docker)         |

---

## Syntax explained

### Variables

```makefile
COMPOSE ?= docker compose
```

Declares a variable. `?=` means "assign this value only if the variable is not
already set in the environment". You can override it at call time:

```sh
COMPOSE="docker-compose" make up   # force the older V1 CLI
```

Reference a variable anywhere with `$(NAME)`.

---

### `.PHONY`

```makefile
.PHONY: help build up down logs restart clean test ...
```

Declares that these target names are **not files on disk**. Without `.PHONY`, if a
file named `build` or `test` existed in the project root, Make would see it as
already up-to-date and skip the recipe entirely. Listing a target in `.PHONY`
forces the recipe to always run.

---

### Targets and recipes

```makefile
target-name: ## Description shown in help
    shell command here
```

- The **target name** comes before the colon.
- The `## Description` comment is picked up by the `awk` script in the `help`
  target and printed as the help text.
- The **recipe** (one or more shell commands) must be indented with a **tab** —
  Make will error on spaces.
- Prefix a command with `@` to suppress Make from printing the command itself
  before it runs.

---

### Prerequisites (dependency chaining)

```makefile
restart: down up
```

Lists other targets as dependencies. Make runs `down` first, then `up`, before
executing any recipe of its own. `restart` has no recipe — the dependencies do
all the work.

---

### Chaining shell commands

```makefile
dev-backend:
    cd backend && python3 manage.py migrate && python manage.py runserver
```

Each recipe line runs in its own sub-shell, so a bare `cd` in one line does not
affect the next line. Chaining with `&&` keeps all commands in the same sub-shell
and stops execution if any earlier command fails.

---

## Target-by-target breakdown

### `help`

```makefile
help: ## Show this help
    @awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
```

Scans the Makefile for lines matching `target: ## description` and prints a
colour-formatted table. `$(MAKEFILE_LIST)` is a built-in Make variable that
expands to the path of the current Makefile.

---

### `build`

```makefile
build: ## Build all Docker images
    $(COMPOSE) build
```

Equivalent to `docker compose build`. Builds fresh images for both the `backend`
and `frontend` services defined in `docker-compose.yml`.

---

### `up`

```makefile
up: ## Start the stack in the background
    $(COMPOSE) up -d
```

`-d` = detached mode. Both containers start in the background and your terminal
is returned to you immediately. The backend container runs migrations automatically
on first start.

---

### `down`

```makefile
down: ## Stop and remove containers (keeps the SQLite volume)
    $(COMPOSE) down
```

Stops and removes the containers and the default bridge network. The named
`backend-data` volume is **preserved**, so your SQLite data survives.

---

### `logs`

```makefile
logs: ## Tail logs from all services
    $(COMPOSE) logs -f
```

`-f` streams new log lines as they arrive. Press `Ctrl+C` to exit without
stopping the containers.

---

### `restart`

```makefile
restart: down up ## Restart the stack
```

No recipe — just prerequisites. Make runs `down` then `up` in order.

---

### `clean`

```makefile
clean: ## Stop the stack and DROP all volumes, images and networks
    $(COMPOSE) down -v --rmi local --remove-orphans
```

| Flag               | Effect                                                        |
| ------------------ | ------------------------------------------------------------- |
| `-v`               | Delete named volumes — **SQLite data is permanently removed** |
| `--rmi local`      | Delete locally built images (not registry-pulled images)      |
| `--remove-orphans` | Remove containers for services no longer in the Compose file  |

Use this for a completely clean slate before a fresh `make build && make up`.

---

### `backend-shell`

```makefile
backend-shell: ## Open a shell inside the backend container
    $(COMPOSE) exec backend sh
```

Opens an interactive `sh` session inside the running `backend` container. The
stack must already be up (`make up`) before using this. Useful for one-off
`manage.py` commands or inspecting the filesystem inside the container.

---

### `migrate`

```makefile
migrate: ## Apply Django migrations
    $(COMPOSE) exec backend python3 manage.py migrate
```

Runs `manage.py migrate` inside the running container. Use this after pulling
new code that includes new migration files.

---

### `test`

```makefile
test: ## Run backend tests inside the container
    $(COMPOSE) exec backend python3 manage.py test
```

Runs the Django test suite inside the running container. The stack must be up.

---

### `createsuperuser`

```makefile
createsuperuser: ## Create a Django admin superuser (interactive)
    $(COMPOSE) exec -it backend python3 manage.py createsuperuser
```

Opens an **interactive** prompt inside the running backend container to create an
admin account. The `-it` flags allocate a TTY so you can type the username,
email, and password. The stack must be up (`make up`) first.

Once created, log in at `http://localhost:8000/admin/`.

---

### `backend-install`

```makefile
backend-install: ## Install Python deps locally (no Docker)
    cd backend && pip install -r requirements.txt
```

Installs Python dependencies into your local virtual environment. Activate the
venv first — see the local development section of the main README.

---

### `frontend-install`

```makefile
frontend-install: ## Install frontend deps locally (no Docker)
    cd frontend && npm install
```

Installs Node dependencies into `frontend/node_modules/`.

---

### `dev-backend`

```makefile
dev-backend: ## Run Django dev server locally
    cd backend && python3 manage.py migrate && python manage.py runserver
```

Applies any pending migrations then starts the Django development server at
`http://localhost:8000`. Requires the virtual environment to be active.

---

### `dev-frontend`

```makefile
dev-frontend: ## Run Next.js dev server locally
    cd frontend && npm run dev
```

Starts the Next.js development server at `http://localhost:3000`.
