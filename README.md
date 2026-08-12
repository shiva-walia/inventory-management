# Inventory Management API

A full-stack inventory management system with a **FastAPI** backend, **PostgreSQL** database, **JWT authentication**, and a dark, industrial-themed **Streamlit** dashboard for stock tracking, low-stock alerts, and audit logging.

**Live Dashboard:** [Add your Streamlit Cloud URL]
**Live API:** [Add your Render URL]
**API Docs:** `<render-url>/docs` (interactive Swagger UI)

---

## Overview

The system manages products, categories, suppliers, and stock transactions, with automatic low-stock alerts and an audit log of inventory changes. The backend is a fully async FastAPI service; the frontend is a single-page Streamlit dashboard styled with a custom dark sidebar and monospace/sans typography (IBM Plex).

---

## Features

- **JWT authentication** — bcrypt-hashed passwords, token-protected routes on every module except `/auth`
- **Product, category & supplier management** — full CRUD with relational integrity (products link to categories via foreign key)
- **Stock transactions** — inbound/outbound movement logging, plus a bulk-adjust endpoint for updating multiple products at once
- **Reports** — low-stock alerts, inventory summary, and an audit log endpoint
- **Fully async backend** — SQLAlchemy 2.0 async ORM with `asyncpg`
- **Custom Streamlit dashboard** — dark sidebar, IBM Plex Sans/Mono typography, status-coded badges (ok / warning / critical)
- **Cloud deployed** — backend on Render, dashboard on Streamlit Cloud, database on Neon (hosted PostgreSQL)

---

## Tech Stack

| Layer          | Technology                                   |
|----------------|-----------------------------------------------|
| Backend API    | FastAPI 0.115, Uvicorn                        |
| ORM / DB Driver| SQLAlchemy 2.0 (async), asyncpg                |
| Database       | PostgreSQL (hosted on Neon)                    |
| Authentication | JWT (`python-jose`) + `bcrypt` password hashing|
| Frontend       | Streamlit 1.35, Pandas, Requests               |
| Backend Hosting| Render                                         |
| Dashboard Hosting | Streamlit Cloud                             |

---

## Architecture

```
┌────────────────────┐   HTTPS    ┌──────────────────────┐   asyncpg   ┌────────────────────┐
│  Streamlit Dashboard │ ─────────▶ │   FastAPI Backend      │ ──────────▶ │   PostgreSQL (Neon)  │
│  (Streamlit Cloud)   │            │   (Render)              │             │                      │
└────────────────────┘            └──────────────────────┘             └────────────────────┘
                                       │
                                       │ JWT-protected routers:
                                       │ categories · suppliers · products
                                       │ transactions · reports
                                       ▼
                                  /auth (register, login, me)
```

---

## Project Structure

```
inventory-management/
└── inventory-clean/
    ├── backend/
    │   ├── app/
    │   │   ├── main.py              # FastAPI app + router registration
    │   │   ├── db/
    │   │   │   └── database.py      # Async engine, session, Base
    │   │   ├── models/
    │   │   │   └── models.py        # SQLAlchemy models
    │   │   ├── schemas/
    │   │   │   └── schemas.py       # Pydantic request/response schemas
    │   │   └── routers/
    │   │       ├── auth.py          # Register, login, JWT, get_current_user
    │   │       ├── products.py
    │   │       ├── categories.py
    │   │       ├── suppliers.py
    │   │       ├── transactions.py
    │   │       └── reports.py
    │   ├── requirements.txt
    │   └── render.yaml              # Render deployment config
    └── frontend/
        ├── dashboard.py             # Streamlit dashboard (single file)
        ├── requirements.txt
        ├── .streamlit/config.toml
        └── assets/login-bg.jpg
```

---

## Database Schema

| Table                | Key Columns                                                                 |
|-----------------------|------------------------------------------------------------------------------|
| `categories`          | `id`, `name` (unique), `description`, `created_at`                          |
| `suppliers`           | `id`, `name`, `contact_name`, `email`, `phone`, `address`, `created_at`     |
| `products`            | `id`, `sku` (unique), `name`, `category_id` (FK), `unit_price`, `stock_qty`, `reorder_level`, `created_at`, `updated_at` |
| `stock_transactions`  | `id`, `product_id` (FK), `txn_type`, `quantity`, `reference_note`, `created_by`, `created_at` |

- `products.category_id` → `categories.id` (`ON DELETE SET NULL`)
- `stock_transactions.product_id` → `products.id` (`ON DELETE CASCADE`)

---

## API Endpoints

### Auth (`/auth`) — public
| Method | Endpoint          | Description                     |
|--------|--------------------|-----------------------------------|
| POST   | `/auth/register`   | Register a new user (bcrypt-hashed password) |
| POST   | `/auth/login`       | Login, returns JWT access token  |
| GET    | `/auth/me`          | Get current authenticated user   |

### Categories (`/categories`) — JWT required
| Method | Endpoint              | Description         |
|--------|-------------------------|------------------------|
| GET    | `/categories/`          | List all categories   |
| POST   | `/categories/`          | Create a category     |
| DELETE | `/categories/{id}`      | Delete a category     |

### Suppliers (`/suppliers`) — JWT required
| Method | Endpoint              | Description         |
|--------|-------------------------|------------------------|
| GET    | `/suppliers/`           | List all suppliers    |
| POST   | `/suppliers/`           | Create a supplier     |
| GET    | `/suppliers/{id}`       | Get supplier details  |

### Products (`/products`) — JWT required
| Method | Endpoint              | Description             |
|--------|-------------------------|----------------------------|
| GET    | `/products/`            | List products             |
| GET    | `/products/stats`       | Aggregate product stats   |
| GET    | `/products/{id}`        | Get product details       |
| POST   | `/products/`            | Create a product          |
| PATCH  | `/products/{id}`        | Update a product          |
| DELETE | `/products/{id}`        | Delete a product          |

### Transactions (`/transactions`) — JWT required
| Method | Endpoint                            | Description                          |
|--------|---------------------------------------|-----------------------------------------|
| POST   | `/transactions/`                      | Record a stock transaction (in/out)    |
| GET    | `/transactions/`                      | List transactions                      |
| POST   | `/transactions/bulk-adjust`           | Adjust stock for multiple products     |
| GET    | `/transactions/product-detail/{id}`   | Transaction history for a product      |

### Reports (`/reports`) — JWT required
| Method | Endpoint                    | Description                     |
|--------|--------------------------------|-------------------------------------|
| GET    | `/reports/low-stock`           | Products at/below reorder level   |
| GET    | `/reports/inventory-summary`   | Summary stats across inventory    |
| GET    | `/reports/audit-log`           | Recent inventory activity (default limit: 100) |

Full interactive docs are auto-generated by FastAPI at `/docs`.

---

## Getting Started

### Prerequisites
- Python 3.10+
- A PostgreSQL database (e.g. a free [Neon](https://neon.tech) instance)

### Backend Setup

```bash
git clone https://github.com/shiva-walia/inventory-management.git
cd inventory-management/inventory-clean/backend

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<dbname>
SECRET_KEY=<your-jwt-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Run the API:
```bash
uvicorn app.main:app --reload
```
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd inventory-management/inventory-clean/frontend
pip install -r requirements.txt
```

Set the backend URL via Streamlit secrets (`.streamlit/secrets.toml`) or an environment variable:
```toml
API_URL = "http://localhost:8000"
```

Run the dashboard:
```bash
streamlit run dashboard.py
```

---

## Deployment

- **Backend** — deployed on [Render](https://render.com) using the included `render.yaml`; environment variables (`DATABASE_URL`, `SECRET_KEY`) are set in the Render dashboard, not committed to the repo.
- **Frontend** — deployed on [Streamlit Cloud](https://streamlit.io/cloud); `API_URL` is set via Streamlit secrets, pointing to the live Render backend.
- **Database** — hosted on [Neon](https://neon.tech), a serverless PostgreSQL provider.

---

## Security Notes

- Passwords are hashed with `bcrypt` before storage — never stored in plaintext.
- JWT secret and database URL are loaded from environment variables (`.env` / Render secrets), not hardcoded.
- All inventory-modifying routes require a valid JWT (`Depends(get_current_user)`), enforced at the router level in `main.py`.

---

## Screenshots

*(Add 2-3 screenshots here — the login screen, main dashboard, and a report view work well.)*

```
![Dashboard](screenshots/dashboard.png)
![Low Stock Report](screenshots/low-stock.png)
```

---

## Future Improvements

- [ ] Role-based access control (admin vs. staff)
- [ ] Automated low-stock email/notification alerts
- [ ] Exportable inventory reports (CSV/PDF)
- [ ] Automated tests for routers and auth flow

---

## Author

**Shiva Walia**
[GitHub](https://github.com/shiva-walia) · [LinkedIn](https://www.linkedin.com/in/shiva-walia-85407a329/)
