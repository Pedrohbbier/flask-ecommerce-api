# E-commerce RESTful API

A RESTful API for a small e-commerce domain, built with **Flask**, **Flask-SQLAlchemy**,
**Flask-Migrate**, **Marshmallow** and **MySQL 8**, running on Docker.

Interactive documentation (Swagger UI): **http://localhost:5001/docs**

---

## 1. Domain model

Three entities and two explicit relationships:

```
Category ──1:N──> Product ──N:N──> Order
                        (through OrderItem)
```

| Entity | Description |
| --- | --- |
| `Category` | Groups products. A category cannot be deleted while it owns products. |
| `Product` | Catalog item. Belongs to exactly one category (`category_id`, `ON DELETE RESTRICT`). |
| `Order` | Customer order with a status lifecycle. Its total is always computed server-side. |
| `OrderItem` | Association object between `Order` and `Product`, carrying `quantity` and a `unit_price` snapshot. |

### Why `OrderItem` is an association *object* and not a plain join table
The N:N link needs its own attributes: the ordered `quantity` and the price at the
moment of purchase. Storing `unit_price` on the line (instead of reading it from the
product) keeps historical orders correct when a product price later changes.

### Referential integrity
* `products.category_id` → `categories.id` with `ON DELETE RESTRICT` — the database itself
  refuses to orphan a product.
* `order_items.order_id` → `orders.id` with `ON DELETE CASCADE` — deleting an order removes its lines.
* `order_items.product_id` → `products.id` with `ON DELETE RESTRICT` — a product that was ordered
  cannot be erased from history.
* `UNIQUE (order_id, product_id)` — the same product can never appear twice in one order.
* `CHECK` constraints: `price > 0`, `stock >= 0`, `quantity >= 1`.

### Business rules (service layer)
* Creating an order (or adding an item) **reserves stock**; canceling or deleting it **returns stock**.
* An order can only be modified while its status is `PENDING` → otherwise `409 Conflict`.
* Status transitions: `PENDING → PAID | CANCELED`, `PAID → SHIPPED | CANCELED`,
  `SHIPPED` and `CANCELED` are final.
* `total_amount` is never accepted from the client; it is recalculated from the items.

---

## 2. Architecture

Four layers, each with a single responsibility:

```
app/
├── __init__.py             # application factory (create_app)
├── config.py               # configuration classes fed by .env
├── extensions.py           # db, migrate, api instances (avoids circular imports)
├── cli.py                  # custom commands: flask seed / flask wipe
├── api/v1/
│   ├── blueprints.py       # the Blueprint objects of the version
│   └── routes/             # ROUTES      — URL table: path -> controller
├── controllers/            # CONTROLLERS — handle the request/response
├── services/               # SERVICES    — business logic + transaction
├── models/                 # MODELS      — tables, columns, relationships
├── schemas/                # Marshmallow — validation and serialization
└── errors/                 # domain exceptions + global error handlers
```

The dependency direction is always **routes → controllers → services → models**.
No layer ever calls upwards.

| Layer | Responsibility | Never does |
| --- | --- | --- |
| `api/v1/routes/` | Maps each path and verb to a controller | Any logic at all |
| `controllers/` | Handles the request: receives the validated payload, calls the service, returns the data and the status code | Business decisions or database access |
| `services/` | Business rules, queries, invariants and the transaction | Import Flask or touch the request |
| `models/` | Shape of the data and the relationships | Contain use-case logic |

A route is nothing but a URL table:

```python
# app/api/v1/routes/product_routes.py
blp.route("")(ProductCollectionController)
blp.route("/<int:product_id>")(ProductController)
```

A controller only translates HTTP. The schema decorators validate the incoming
payload and serialize the response, and they are also what generates the Swagger
documentation:

```python
# app/controllers/product_controller.py
class ProductController(MethodView):
    @blp.arguments(ProductPatchSchema)
    @blp.response(200, ProductSchema)
    def patch(self, payload, product_id):
        """Partial update: typical use cases are price and stock adjustments."""
        return product_service.update_product(product_id, ensure_not_empty(payload))
```

And the service holds every decision — uniqueness of the SKU, existence of the
category, stock reservation, allowed status transitions, recalculation of the total.

### Transaction boundary
Every write in a service runs inside the `transaction()` context manager
(`app/services/transaction.py`), which commits on success and rolls back if any
rule rejects the operation. That is what makes a use case atomic: if the second
item of an order has no stock, the units reserved for the first one are never
persisted, and no half-built order reaches the database.

### Error handling
The service layer never imports Flask: it raises domain exceptions
(`ResourceNotFoundError`, `ConflictError`, `BusinessRuleError`, `ValidationError`)
and `app/errors/handlers.py` translates them into the standard JSON response.
That is what keeps the rules testable and the controllers trivial.

---

## 3. Running the project

Requirements: Docker and Docker Compose.

```bash
make setup   # creates .env from .env.example
make up      # builds the image, starts MySQL + API, applies the migrations
make seed    # loads demo data (4 categories, 12 products, 3 orders)
```

Then open:

* **API + Swagger UI** — http://localhost:5001/docs
* **phpMyAdmin** — http://localhost:8080 (already signed in as the `MYSQL_USER` from `.env`)

> The API is published on port **5001** because macOS reserves port 5000 for the
> AirPlay Receiver. Change `APP_PORT` in `.env` if you prefer another port.

Useful commands (`make help` lists them all):

| Command | Description |
| --- | --- |
| `make up` | Start the whole stack in the background |
| `make down` | Stop the containers |
| `make logs` | Follow the API logs |
| `make reset` | Wipe volumes, rebuild, migrate and seed from scratch |
| `make migrate m="message"` | Autogenerate a new migration |
| `make upgrade` / `make downgrade` | Apply / roll back migrations |
| `make seed` / `make wipe` | Load / delete demo data |
| `make db-shell` | Open a MySQL client on the database |
| `make pma` | Open phpMyAdmin in the browser |
| `make shell` | Open a shell inside the API container |

The API container waits for the MySQL healthcheck and runs `flask db upgrade`
automatically before starting (see `docker/entrypoint.sh`).

### Configuration
All settings come from environment variables (`.env`, never committed):
`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`,
`SECRET_KEY`, `APP_PORT`, `PMA_PORT`, `FLASK_ENV`, `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`.

---

## 4. Endpoints

Base path: `/api/v1`

### Categories
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/categories` | List with `?name=&page=&per_page=&sort_by=&order=` |
| `GET` | `/categories/{id}` | Retrieve one category |
| `GET` | `/categories/{id}/products` | Products of the category (1:N navigation) |
| `POST` | `/categories` | Create → `201` |
| `PUT` | `/categories/{id}` | Full update |
| `PATCH` | `/categories/{id}` | Partial update |
| `DELETE` | `/categories/{id}` | Delete → `204`, or `409` if it still has products |

### Products
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/products` | List with `?q=&category_id=&min_price=&max_price=&is_active=&in_stock=&page=&per_page=&sort_by=&order=` |
| `GET` | `/products/{id}` | Retrieve one product (with its category) |
| `POST` | `/products` | Create → `201` |
| `PUT` | `/products/{id}` | Full update |
| `PATCH` | `/products/{id}` | Partial update (price, stock, …) |
| `DELETE` | `/products/{id}` | Delete → `204`, or `409` if it belongs to an order |

### Orders
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/orders` | List with `?status=&customer_email=&page=&per_page=&sort_by=&order=` |
| `GET` | `/orders/{id}` | Retrieve one order with all of its items |
| `POST` | `/orders` | Create, reserving stock → `201` |
| `PUT` | `/orders/{id}` | Replace customer data and the whole item set |
| `PATCH` | `/orders/{id}` | Partial update, typically a status transition |
| `DELETE` | `/orders/{id}` | Delete → `204`, returning the reserved stock |
| `POST` | `/orders/{id}/items` | Add a product to a pending order → `201` |
| `PATCH` | `/orders/{id}/items/{item_id}` | Change the quantity of a line |
| `DELETE` | `/orders/{id}/items/{item_id}` | Remove a line → `204` |

### Utility
| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Liveness probe (API + database) |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/openapi.json` | OpenAPI 3.0.3 specification |

---

## 5. Status codes and error handling

| Code | When |
| --- | --- |
| `200 OK` | Successful `GET`, `PUT`, `PATCH` |
| `201 Created` | Successful `POST` |
| `204 No Content` | Successful `DELETE` (empty body) |
| `400 Bad Request` | Malformed request (e.g. invalid JSON syntax) |
| `404 Not Found` | Unknown resource or identifier |
| `405 Method Not Allowed` | Verb not supported by the route |
| `409 Conflict` | Conflict with the current state (duplicated unique value, non-editable order, invalid status transition, delete blocked by a relationship) |
| `422 Unprocessable Entity` | Payload validation / typing / business rule failure |
| `500 Internal Server Error` | Unexpected error |

Every failure returns the same JSON envelope, produced by the global handlers in
`app/errors/handlers.py`:

```json
{
  "error": "Validation error",
  "details": { "json": { "price": ["Price must be greater than zero."] } }
}
```

---

## 6. Example requests

```bash
BASE=http://localhost:5001/api/v1

# Create a category
curl -X POST $BASE/categories -H 'Content-Type: application/json' \
  -d '{"name": "Electronics", "description": "Phones, laptops and gadgets"}'

# Create a product in that category
curl -X POST $BASE/products -H 'Content-Type: application/json' \
  -d '{"name":"Wireless Mouse","sku":"ELEC-001","price":"89.90","stock":120,"category_id":1}'

# Filter and paginate products
curl "$BASE/products?q=mouse&min_price=50&in_stock=true&sort_by=price&order=desc&page=1&per_page=10"

# Create an order (stock is reserved, total is computed server-side)
curl -X POST $BASE/orders -H 'Content-Type: application/json' \
  -d '{"customer_name":"Alice Johnson","customer_email":"alice@example.com",
       "items":[{"product_id":1,"quantity":2},{"product_id":5,"quantity":1}]}'

# Add another product to the order
curl -X POST $BASE/orders/1/items -H 'Content-Type: application/json' \
  -d '{"product_id":2,"quantity":1}'

# Confirm payment (status transition)
curl -X PATCH $BASE/orders/1 -H 'Content-Type: application/json' -d '{"status":"PAID"}'

# Adjust only the stock of a product (partial update)
curl -X PATCH $BASE/products/1 -H 'Content-Type: application/json' -d '{"stock":200}'

# Delete an order (stock goes back to the catalog)
curl -X DELETE $BASE/orders/1 -i
```

---

## 7. Running without Docker (optional)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point MYSQL_HOST to your local MySQL server
export FLASK_APP=wsgi.py
flask db upgrade
flask seed
flask run
```

---

## 8. Tech stack

| Concern | Choice |
| --- | --- |
| Web framework | Flask 3 |
| ORM | Flask-SQLAlchemy 3 / SQLAlchemy 2 |
| Migrations | Flask-Migrate (Alembic) |
| Validation & serialization | Marshmallow |
| OpenAPI / Swagger UI | flask-smorest (spec generated from the Marshmallow schemas) |
| Database | MySQL 8 (PyMySQL driver) |
| Configuration | python-dotenv |
| Database GUI | phpMyAdmin |
| Containers | Docker + Docker Compose |
