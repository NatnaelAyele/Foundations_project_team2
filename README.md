# FreshLink

FreshLink is a harvest-coordination platform for connecting farmers, transport providers, and cold-storage hubs. It supports provider registration, role-based dashboards, harvest forecasting, transport and storage allocation, USSD farmer interaction, notification records, and payment workflow integration.

The application is built around a FastAPI backend, PostgreSQL database, SQLAlchemy models, a coordination engine, and static dashboard pages served by the backend.

## Core capabilities

- Provider registration for transport providers and storage hub providers.
- Login with role-based access for administrators, transport providers, and storage providers.
- Protected admin, transporter, and storage hub dashboards.
- Farmer registration and harvest forecast management by administrators.
- Transporter truck management, availability updates, trip views, pickup, and delivery actions.
- Cold hub capacity management, allocation views, and allocation receipt confirmation.
- Coordination engine for matching forecasts with eligible trucks and cold hubs.
- USSD farmer menus for harvest reporting and viewing information without a web dashboard.
- Notification persistence with optional Africa's Talking SMS delivery.
- Flutterwave payment workflow endpoints and webhook handling.

## Project structure

```text
backend/
  auth/                 Authentication and authorization helpers
  database/             SQLAlchemy connection, models base, and database helpers
  engine/               Coordination, matching, scheduling, and notification logic
  Flutterwave/          Payment gateway implementation
  models/               SQLAlchemy database models
  routes/               FastAPI API and dashboard routes
  services/             Registration, harvest, coordination, and payment services
  main.py               FastAPI application entry point

database/
  schema.sql            PostgreSQL schema
  indexes.sql           Database indexes
  seed_data.sql         Reference seed data
  migrations/           Incremental PostgreSQL migrations

frontend/
  landing_page/         Public landing, registration, and provider login pages
  admin/                Administrator pages and dashboard assets
  transporter_dashboard/
  storagehub_dashboard/
  sevices/              Shared browser API client assets

ussd_gateway/           Farmer USSD menus, sessions, and repositories
sms_gateway/            SMS notification and Africa's Talking integration
  tools/                  Developer-operated utilities, including the terminal SMS inbox viewer
tests/                  Automated test suite
```

## Technology

| Area | Main technologies |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| Database access | SQLAlchemy, psycopg, psycopg2 |
| Primary database | PostgreSQL |
| Authentication | JWT, bcrypt, HTTP-only cookies |
| Scheduling | APScheduler |
| Frontend | HTML, CSS, JavaScript |
| USSD and SMS | Africa's Talking-compatible callback and SMS integration |
| Payments | Flutterwave integration |

## Prerequisites

- Python 3.11 or later.
- PostgreSQL 15 or later.
- Git.
- A Python virtual environment is recommended.

Africa's Talking and Flutterwave accounts are optional for local development. They are required only when testing their respective Sandbox integrations.

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/NatnaelAyele/Foundations_project_team2.git
cd Foundations_project_team2
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and replace its database and secret values:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Do not commit `.env`, database passwords, API keys, webhook secrets, or JWT secrets.

### 5. Create the PostgreSQL database

Create a PostgreSQL database, then configure either the individual variables or `DATABASE_URL` in `.env`.

```env
DATABASE_ENGINE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=freshlink
DATABASE_USER=postgres
DATABASE_PASSWORD=replace_with_a_secure_password
DATABASE_SSL_MODE=prefer
```

Alternatively:

```env
DATABASE_URL=postgresql://username:password@host:5432/freshlink?sslmode=prefer
```

### 6. Initialize the schema

Run the schema and index scripts against the target PostgreSQL database. Apply the migration files in numerical order when the database was created from an earlier schema version.

```bash
psql -U postgres -d freshlink -f database/schema.sql
psql -U postgres -d freshlink -f database/indexes.sql
```

Reference seed data is available in `database/seed_data.sql`. Review it before use, especially account records and password hashes, and use known secure credentials for accounts intended for login.

### 7. Run the application

```bash
uvicorn backend.main:app --reload
```

The application is available at:

- API documentation: `http://127.0.0.1:8000/docs`
- Landing page: `http://127.0.0.1:8000/landing_page/index.html`
- Provider login: `http://127.0.0.1:8000/landing_page/login.html`
- Admin login: `http://127.0.0.1:8000/admin/`
- Database health check: `http://127.0.0.1:8000/health/db`

## Configuration reference

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Secret used to create authentication tokens. Use a strong private value outside local development. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Authentication token lifetime in minutes. |
| `COOKIE_SECURE` | Set to `true` for HTTPS deployments. |
| `DATABASE_URL` | Full PostgreSQL connection URL. Overrides the individual database variables. |
| `DATABASE_ENGINE` | Database engine selector; use `postgresql` for the main application branch. |
| `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` | PostgreSQL server location and database name. |
| `DATABASE_USER`, `DATABASE_PASSWORD` | PostgreSQL account credentials. |
| `DATABASE_SSL_MODE` | PostgreSQL SSL mode, such as `prefer` or `require`. |
| `CORS_ORIGINS` | Comma-separated browser origins permitted to call the API. |
| `ENGINE_SCHEDULER_ENABLED` | Enables the background coordination scheduler. |
| `ENGINE_RUN_INTERVAL_HOURS` | Interval between scheduled coordination runs. |
| `ENGINE_RUN_ON_FORECAST_CREATED` | Runs coordination after a new forecast is created when enabled. |
| `FLUTTERWAVE_*` | Flutterwave Sandbox or production credentials and webhook verification settings. |

## Authentication and roles

The dashboard roles are:

| Role value | Access |
|---|---|
| `admin` | Administrative dashboard, farmers, forecasts, reports, and coordination controls. |
| `truck_provider` | Transport provider dashboard, owned trucks, availability, and assigned trips. |
| `hub_operator` | Storage hub dashboard, hub capacity, allocations, and receipt confirmation. |

Administrators are created manually or through approved seed data. Farmers use USSD rather than the dashboard login flow.

Login returns a role-specific dashboard URL and also sets an HTTP-only authentication cookie. Protected routes verify the authenticated user's role before serving their dashboard or role-specific data.

## API overview

The main API groups are listed below.

| Area | Base path | Examples |
|---|---|---|
| Accounts | `/api` | `POST /registrations/providers`, `POST /auth/login`, `POST /auth/logout` |
| Admin | `/api/admin` | sectors, farmers, forecasts, reports, dashboard summary, coordination runs |
| Transporter | `/api/transporter` | profile, dashboard, trucks, trips, pickup, delivery |
| Storage hub | `/api/hub` | profile, capacity, dashboard, allocations, receipt confirmation |
| Payments | `/api/payments` | initialization, verification, refund, Flutterwave webhook and callback |
| USSD | `/api/ussd` | Africa's Talking-compatible USSD callback |
| Health | `/health`, `/health/db` | service and database status |

Use the interactive OpenAPI interface at `/docs` for request and response schemas.

## Coordination engine

The coordination engine evaluates pending harvest forecasts and identifies eligible trucks and cold hubs based on availability, capacity, sector, and operational status. Its results are persisted as coordination plans and allocations for the dashboards to display.

The scheduler is configured through environment variables. In the normal configuration it runs at the interval defined by `ENGINE_RUN_INTERVAL_HOURS`. A development-style immediate trigger can be enabled with `ENGINE_RUN_ON_FORECAST_CREATED`.

## USSD integration

The deployed USSD callback endpoint is:

```text
https://your-domain.example/api/ussd
```

For Africa's Talking Sandbox:

1. Create a Sandbox USSD channel/service code.
2. Set its callback URL to the public `/api/ussd` endpoint.
3. Use Africa's Talking's USSD Simulator to test the menu flow.
4. Use a phone number belonging to a registered farmer in the database.

The callback accepts Africa's Talking form fields such as `sessionId`, `serviceCode`, `phoneNumber`, and `text`, and returns responses beginning with `CON` or `END`.

The basic USSD callback does not require Africa's Talking API credentials in the application. It requires only a public HTTPS endpoint configured in the Africa's Talking Sandbox.

## SMS integration

Notification records are created in the database by application workflows. Outbound Africa's Talking SMS delivery is optional and disabled unless explicitly configured.

Add the following server-side environment variables when using the Africa's Talking Sandbox:

```env
AT_USERNAME=sandbox
AT_API_KEY=your_africas_talking_sandbox_api_key
AT_SMS_ENABLED=true
```

Sandbox SMS messages appear in the Africa's Talking Sandbox environment rather than on real handsets.

The terminal notification viewer is available as a developer tool:

```bash
python -m tools.terminal_sms_inbox
```

It can also be run directly from VS Code using the Run Python File action.

## Payment integration

Payment endpoints are implemented through Flutterwave. Configure the Flutterwave variables in `.env` before testing payment initialization, verification, webhook handling, or callbacks.

Use Flutterwave Sandbox credentials during development. Do not use production credentials in a local `.env` that may be shared, committed, or displayed in screenshots.

## Database and schema notes

- The primary application database is PostgreSQL.
- SQLAlchemy models are in `backend/models/`.
- The canonical PostgreSQL schema is `database/schema.sql`.
- Database indexes are defined in `database/indexes.sql`.
- Migration files preserve incremental schema evolution in `database/migrations/`.

## Testing

Automated tests are stored in `tests/`. The test suite is being refreshed, so test results should be generated from the current tests and an isolated PostgreSQL test database rather than assumed from historical test files.

Recommended testing layers are:

1. Unit tests for authentication, validation, matching rules, and helper functions.
2. API validation tests for invalid input and authorization failures.
3. Integration tests for registration, login, database persistence, engine allocation, and dashboard data.
4. Functional tests for complete admin, transporter, storage-provider, and USSD workflows.
5. Sandbox tests for Africa's Talking and Flutterwave after external credentials are configured.

Run the suite with:

```bash
pytest
```

## Deployment

FreshLink is deployed at:

```text
https://natnael.tech
```

The deployment uses three Ubuntu servers:

| Server role | Host label | Responsibility |
|---|---|---|
| Load balancer | `lb-01` | HAProxy, public HTTPS entry point, TLS certificate handling, and traffic distribution. |
| Application server | `wb-01` | Nginx reverse proxy, FreshLink FastAPI container, PostgreSQL database host, and the active coordination scheduler. |
| Application server | `wb-02` | Nginx reverse proxy and a second FreshLink FastAPI container. |

The request path is:

```text
Browser or external provider
        |
        v
HAProxy on lb-01 (HTTPS/TLS)
        |
        +----> Nginx on wb-01 ----> FreshLink FastAPI container
        |
        +----> Nginx on wb-02 ----> FreshLink FastAPI container
                                      |
                                      v
                         Shared PostgreSQL database on wb-01
```

HAProxy distributes incoming traffic across the two application servers. Nginx serves optimized static assets directly and proxies application requests to the FastAPI container running locally on each web server. Both application instances use the same PostgreSQL database, which keeps dashboard, API, engine, and USSD data consistent regardless of which server handles a request.

HTTPS is terminated at the load balancer for `natnael.tech` and `www.natnael.tech`. Backend application servers communicate only with the load balancer and the database services required for the deployment.

Only one application server runs the coordination scheduler. This prevents the two load-balanced FastAPI instances from starting duplicate coordination jobs against the same database.