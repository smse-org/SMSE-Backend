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

## API Endpoints

Find the API documentation [here](https://smseai.me/api/docs) as well as usage examples.