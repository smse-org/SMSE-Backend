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

- **URL:** `/api/v1/auth/register`
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

- **URL:** `/api/v1/auth/login`
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

#### Refresh

- **URL:** `/api/v1/auth/refresh`
- **Method:** `POST`
- **Description:** Refresh a JWT token.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_REFRESH_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Token refreshed successfully.
    ```json
    {
      "access_token": "string"
    }
    ```
  - `401 Unauthorized`: Token expired or invalid.
    ```json
    {
      "msg": "Token has expired"
    }
    ```
    ```json
    {
      "msg": "Invalid token"
    }
    ```


#### Logout

- **URL:** `/api/v1/auth/logout`
- **Method:** `POST`
- **Description:** Logout a user and revoke the JWT token.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Logout successful.
    ```json
    {
      "msg": "Logout successful"
    }
    ```
  - `401 Unauthorized`: Invalid token.
    ```json
    {
      "msg": "Invalid token"
    }
    ```


#### Protected

- **URL:** `/api/v1/auth/protected`
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

- **URL:** `/api/v1/users/me`
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

- **URL:** `/api/v1/users/me`
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

- **URL:** `/api/v1/users/me`
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

### Content Endpoints

#### Create Content

- **URL:** `/api/v1/contents`
- **Method:** `POST`
- **Description:** Upload a new content file.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Request Body:**
  - Multipart form data with a file field.
- **Responses:**
  - `201 Created`: Content created successfully.
    ```json
    {
      "message": "Content created successfully",
      "content": {
        "id": "integer",
        "content_path": "string",
        "content_tag": "boolean"
      }
    }
    ```
  - `400 Bad Request`: No file part or file type not allowed.
    ```json
    {
      "msg": "No file part"
    }
    ```
    ```json
    {
      "msg": "No selected file"
    }
    ```
    ```json
    {
      "msg": "File type not allowed"
    }
    ```
  - `500 Internal Server Error`: Error creating content.
    ```json
    {
      "message": "Error creating content"
    }
    ```

#### Get All Contents

- **URL:** `/api/v1/contents`
- **Method:** `GET`
- **Description:** Get all contents for the authenticated user.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns a list of contents.
    ```json
    {
      "contents": [
        {
          "id": "integer",
          "content_path": "string",
          "content_tag": "boolean"
        }
      ]
    }
    ```

#### Get Content

- **URL:** `/api/v1/contents/<int:content_id>`
- **Method:** `GET`
- **Description:** Get a specific content by its ID.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns the content details.
    ```json
    {
      "content": {
        "id": "integer",
        "content_path": "string",
        "content_tag": "boolean"
      }
    }
    ```
  - `404 Not Found`: Content not found.
    ```json
    {
      "message": "Content not found"
    }
    ```

#### Update Content

- **URL:** `/api/v1/contents/<int:content_id>`
- **Method:** `PUT`
- **Description:** Update a specific content by its ID.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "content_tag": "boolean"
  }
  ```
- **Responses:**
  - `200 OK`: Content updated successfully.
    ```json
    {
      "message": "Content updated successfully",
      "content": {
        "id": "integer",
        "content_path": "string",
        "content_tag": "boolean"
      }
    }
    ```
  - `404 Not Found`: Content not found.
    ```json
    {
      "message": "Content not found"
    }
    ```
  - `500 Internal Server Error`: Error updating content.
    ```json
    {
      "message": "Error updating content"
    }
    ```

#### Delete Content

- **URL:** `/api/v1/contents/<int:content_id>`
- **Method:** `DELETE`
- **Description:** Delete a specific content by its ID.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Content deleted successfully.
    ```json
    {
      "message": "Content deleted successfully"
    }
    ```
  - `404 Not Found`: Content not found.
    ```json
    {
      "message": "Content not found"
    }
    ```
  - `500 Internal Server Error`: Error deleting content.
    ```json
    {
      "message": "Error deleting content"
    }
    ```

#### Download Content

- **URL:** `/api/v1/contents/<int:content_id>/download`
- **Method:** `GET`
- **Description:** Download a specific content file by its ID.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns the content file.
  - `404 Not Found`: Content or file not found.
    ```json
    {
      "message": "Content not found"
    }
    ```
    ```json
    {
      "message": "File not found"
    }
    ```

#### Get Allowed Extensions

- **URL:** `/api/v1/contents/allowed_extensions`
- **Method:** `GET`
- **Description:** Get the list of allowed file extensions for content uploads.
- **Responses:**
  - `200 OK`: Returns the list of allowed extensions.
    ```json
    {
      "allowed_extensions": ["string"]
    }
    ```

### Search Endpoints

#### Search Files

- **URL:** `/api/v1/search`
- **Method:** `POST`
- **Description:** Search for files based on a query.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Request Body:**
  ```json
  {
    "query": "string"
  }
  ```
- **Responses:**
  - `201 Created`: Search completed successfully.
    ```json
    {
      "message": "Search completed successfully",
      "query_id": "integer",
      "results": [
        {
          "content_id": "integer",
          "similarity_score": "float"
        }
      ]
    }
    ```
  - `400 Bad Request`: Query text is required.
    ```json
    {
      "message": "Query text is required"
    }
    ```
  - `500 Internal Server Error`: Error creating embedding for query.
    ```json
    {
      "message": "Error creating embedding for query"
    }
    ```

#### Get Query History

- **URL:** `/api/v1/queries`
- **Method:** `GET`
- **Description:** Get the search query history for the authenticated user.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns a list of queries.
    ```json
    [
      {
        "id": "integer",
        "text": "string",
        "timestamp": "string"
      }
    ]
    ```

#### Get Search Results History

- **URL:** `/api/v1/searches/<int:query_id>`
- **Method:** `GET`
- **Description:** Get the search results history for a specific query.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Returns the query details and search results.
    ```json
    {
      "query": {
        "id": "integer",
        "text": "string",
        "timestamp": "string"
      },
      "results": [
        {
          "content_id": "integer",
          "similarity_score": "float",
          "retrieved_at": "string"
        }
      ]
    }
    ```
  - `404 Not Found`: Query not found.
    ```json
    {
      "message": "Query not found"
    }
    ```

#### Delete Query

- **URL:** `/api/v1/queries/<int:query_id>`
- **Method:** `DELETE`
- **Description:** Delete a specific query by its ID.
- **Headers:**
  ```http
  Authorization: Bearer <JWT_TOKEN>
  ```
- **Responses:**
  - `200 OK`: Query deleted successfully.
    ```json
    {
      "message": "Query deleted successfully"
    }
    ```
  - `404 Not Found`: Query not found.
    ```json
    {
      "message": "Query not found"
    }
    ```