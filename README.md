# Shipping API

A robust, production-ready shipping and delivery management API built with Django, MongoDB, and Redis. This project demonstrates scalable backend design, secure authentication, real-time delivery tracking, and thoughtful API design for modern logistics applications.

---

## Project Overview

The Shipping API provides a comprehensive backend for managing users, deliveries, and real-time status updates. It supports user registration, authentication with JWT, admin management, and delivery tracking with geospatial data. The system is designed for extensibility, security, and performance, leveraging MongoDB for flexible data modeling and Redis for fast token management and WebSocket support.

The project was developed with a focus on clean architecture, testability, and maintainability. Key challenges included integrating multiple data stores, ensuring secure authentication, and handling real-time updates. These were overcome through careful design, extensive testing, and iterative improvements.

---

## Features

- **User Management:** Registration, login, logout, and admin creation with secure password hashing.
- **Authentication:** JWT-based authentication, token storage and invalidation with Redis.
- **Authorization:** Fine-grained permissions for regular users and admins.
- **Delivery Management:** CRUD operations for deliveries, including geospatial location and status history.
- **Real-Time Tracking:** WebSocket support for live delivery status updates.
- **Extensive Testing:** High test coverage with pytest, including edge cases and security checks.

---

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB (running locally or accessible remotely)
- Redis (running locally or accessible remotely)
- [Optional] Node.js (for WebSocket client testing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/shipping-api.git
   cd shipping-api
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (if needed):**
   - Edit `logistics_backend/settings.py` for MongoDB/Redis credentials and JWT secret.

5. **Run database seed script (optional, for demo data):**
   ```bash
   python scripts/seed.py
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Run tests:**
   ```bash
   pytest
   ```

---

## API Documentation

### Authentication

- **Register:**  
  `POST /api/v1/users/register/`  
  Body: `{ "username": "...", "email": "...", "password": "..." }`

- **Login:**  
  `POST /api/v1/users/login/`  
  Body: `{ "username": "...", "password": "..." }`  
  Response: `{ "token": "..." }`

- **Logout:**  
  `POST /api/v1/users/logout/`  
  Header: `Authorization: Bearer <token>`

- **Create Admin:**  
  `POST /api/v1/users/create-admin/`  
  Header: `Authorization: Bearer <admin_token>`  
  Body: `{ "username": "...", "email": "...", "password": "..." }`

---

### Deliveries

- **Get Delivery Details:**  
  `GET /api/v1/deliveries/<delivery_id>/`  
  Public endpoint.

- **Get My Deliveries:**  
  `GET /api/v1/deliveries/my/`  
  Header: `Authorization: Bearer <token>`

- **Create Delivery (Admin):**  
  `POST /api/v1/deliveries/`  
  Header: `Authorization: Bearer <admin_token>`  
  Body: `{ "title": "...", "status": "...", "customer_id": "...", ... }`

- **Update Delivery Location (Admin):**  
  `PUT /api/v1/deliveries/<delivery_id>/location/`  
  Header: `Authorization: Bearer <admin_token>`  
  Body: `{ "location": { "type": "Point", "coordinates": [lon, lat] } }`

- **Update Delivery Status (Admin):**  
  `PUT /api/v1/deliveries/<delivery_id>/status/`  
  Header: `Authorization: Bearer <admin_token>`  
  Body: `{ "status": "...", "location": { ... } }`

- **Delete Delivery (Admin):**  
  `DELETE /api/v1/deliveries/<delivery_id>/`  
  Header: `Authorization: Bearer <admin_token>`

---

## Design & Development Approach

This project was built with a strong emphasis on modularity and security.  
- **Authentication and authorization** are handled via custom DRF permission classes, ensuring only authorized users can access sensitive endpoints.
- **Data modeling** leverages MongoDB for flexibility, especially for nested delivery status histories and geospatial queries.
- **Token management** uses Redis for fast, scalable session handling and JWT invalidation.
- **Real-time features** are enabled via Django Channels and Redis, supporting live delivery tracking.
- **Testing** was prioritized from the start, with pytest covering both typical and edge-case scenarios.

Throughout development, trade-offs were carefully considered. For example, MongoDB was chosen over a relational database for its schema flexibility, which is ideal for evolving delivery data. Redis was selected for its speed and suitability for ephemeral token storage.

---

## Reflections & Future Improvements

While the current system is robust and production-ready, there are always areas for growth:
- **API Rate Limiting:** To further secure endpoints.
- **Async Processing:** For even better real-time performance.
- **API Documentation:** Integration with Swagger/OpenAPI for interactive docs.
- **CI/CD Integration:** Automated testing and deployment pipelines.
- **Frontend Client:** A React or mobile client for end-to-end demonstration.

This project reflects a commitment to best practices, continuous improvement, and clear communication—qualities I bring to every engineering challenge.

---

## License

MIT License
