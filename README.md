# SMSE Backend

## Description

This is the backend for the SMSE project. It is a RESTful API that provides endpoints for the frontend to interact with the database and the models.

## Installation

1. Clone the repository
2. Run `poetry install` to install the dependencies
3. Run `poetry shell` to activate the virtual environment
4. Run `flask db upgrade` to create the database
5. Run `smse-backend` to start the server

## Development

If you made changes to the models, you need to run `flask db migrate` to generate a new migration file. After that, you need to run `flask db upgrade` to apply the changes to the database.

## Authentication

1. User Sends Credentials → Login Endpoint
2. Server Validates Credentials
3. Server Generates JWT Token
4. Client Stores Token (usually in localStorage)
5. Client Sends Token with Subsequent Requests
6. Server Validates Token on Protected Routes

## Endpoints

### Auth Endpoints

#### Register

- **URL:** `/auth/register`
- **Method:** `POST`
- **Description:** Register a new user.
- **Request Body:**
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Responses:**
  - `201 Created`: User created successfully.
    ```json
    {
      "msg": "User created successfully"
    }
    ```
  - `400 Bad Request`: Missing required fields or user already exists.
    ```json
    {
      "msg": "Missing required fields"
    }
    ```
    ```json
    {
      "msg": "Username already exists"
    }
    ```
    ```json
    {
      "msg": "Email already exists"
    }
    ```

#### Login

- **URL:** `/auth/login`
- **Method:** `POST`
- **Description:** Login a user and get a JWT token.
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Responses:**
  - `200 OK`: Login successful, returns JWT token.
    ```json
    {
      "access_token": "string"
    }
    ```
  - `401 Unauthorized`: Invalid credentials.
    ```json
    {
      "msg": "Invalid credentials"
    }
    ```

#### Protected

- **URL:** `/auth/protected`
- **Method:** `GET`
- **Description:** A protected route that requires a valid JWT token.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns the username of the authenticated user.
    ```json
    {
      "username": "string"
    }
    ```

### User Endpoints

#### Get User

- **URL:** `/users/me`
- **Method:** `GET`
- **Description:** Get the details of the authenticated user.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns the user details.
    ```json
    {
      "id": "integer",
      "username": "string",
      "email": "string",
      "created_at": "string"
    }
    ```
  - `404 Not Found`: User not found.
    ```json
    {
      "message": "User not found"
    }
    ```

#### Update User

- **URL:** `/users/me`
- **Method:** `PUT`
- **Description:** Update the details of the authenticated user.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "username": "string",
    "email": "string"
  }
  ```
- **Responses:**
  - `200 OK`: User updated successfully.
    ```json
    {
      "message": "User updated successfully",
      "user": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "created_at": "string"
      }
    }
    ```
  - `400 Bad Request`: Username or email already exists, or invalid email format.
    ```json
    {
      "message": "Username already exists"
    }
    ```
    ```json
    {
      "message": "Email already exists"
    }
    ```
    ```json
    {
      "message": "Invalid email address"
    }
    ```
  - `404 Not Found`: User not found.
    ```json
    {
      "message": "User not found"
    }
    ```

#### Delete User

- **URL:** `/users/me`
- **Method:** `DELETE`
- **Description:** Delete the authenticated user.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: User deleted successfully.
    ```json
    {
      "message": "User deleted successfully"
    }
    ```
  - `404 Not Found`: User not found.
    ```json
    {
      "message": "User not found"
    }
    ```