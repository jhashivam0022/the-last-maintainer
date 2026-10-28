# Legacy Shop API

## Authentication
- `POST /api/auth/login` - returns a session token
- `POST /api/auth/refresh` - refreshes an expired token

## Users
- `GET /api/users/{id}` - fetch a user
- `DELETE /api/users/{id}` - remove a user
