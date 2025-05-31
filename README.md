# SMSE Backend

## Description

This is the backend for the SMSE project. It is a RESTful API that provides endpoints for the frontend to interact with the database and the models.

## Installation

1. Clone the repository
2. Run `poetry install` to install the dependencies
3. Run `poetry shell` to activate the virtual environment
4. Run `flask db upgrade` to create the database
    1. if you are using Docker, you can run `docker compose up migrate` to run the migration using the Docker container
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


## SMSE Backend - Storage Configuration

The SMSE backend now supports both local filesystem storage and S3-compatible object storage (like MinIO, AWS S3, etc.). This document explains how to configure and use each storage backend.

## Quick Setup with MinIO (Recommended for Self-Hosting)

### 1. Using Docker Compose (Easiest)

The included `docker-compose.yaml` already has MinIO configured. Just set your environment variables:

```bash
# Copy the example environment file
cp example.env .env

# Edit .env and set:
STORAGE_TYPE=s3
S3_BUCKET_NAME=smse-files
S3_ENDPOINT_URL=http://minio:9000  # Note: Use 'minio' service name, not 'localhost'
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION_NAME=us-east-1
S3_USE_SSL=false

# MinIO admin credentials
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

**Important Docker Networking Note**: When running in Docker Compose, use the service name `minio` instead of `localhost` in the `S3_ENDPOINT_URL`. Docker containers communicate with each other using service names, not `localhost`.

Start the services:
```bash
docker-compose up -d
```

MinIO will be available at:
- **Storage API**: http://localhost:9000 (from host machine)
- **Web Console**: http://localhost:9001 (from host machine)
- **Credentials**: minioadmin / minioadmin

### 2. Manual MinIO Setup

If you prefer to run MinIO separately:

```bash
# Using Docker
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -v /path/to/data:/data \
  minio/minio server /data --console-address ":9001"

# Or using binary
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin ./minio server /path/to/data --console-address ":9001"
```

##  Docker Setup

## File Structure

```
├── Dockerfile              # backend image
├── Dockerfile.worker       # Worker image with SMSE AI
├── docker-compose.yaml     # Development setup
└── pyproject.toml          # SMSE dependencies
```

## Usage

### Development
```bash
# Build and run all services
docker compose up --build

# Run only backend services (without worker)
docker compose up db redis backend
```

### Scaling
```bash
# Scale workers independently
docker compose up --scale worker=3

# Scale backend for load balancing
docker compose up --scale backend=2
```

## Storage Backend Configuration

### Local Storage (Default)

```env
STORAGE_TYPE=local
# Files will be stored in the UPLOAD_FOLDER directory
```

### S3-Compatible Storage

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket-name
S3_ENDPOINT_URL=http://your-s3-endpoint:9000  # MinIO endpoint
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION_NAME=us-east-1
S3_USE_SSL=false  # true for production with TLS
```

### AWS S3 (Production)

```env
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-aws-bucket
# Leave S3_ENDPOINT_URL empty for AWS S3
S3_ACCESS_KEY_ID=your-aws-access-key
S3_SECRET_KEY=your-aws-secret-key
S3_REGION_NAME=your-aws-region
S3_USE_SSL=true
```

## API Compatibility

The storage service maintains full backward compatibility. All existing API endpoints and functionality work exactly the same regardless of the storage backend. The only difference is where files are actually stored.

### File Operations

All file operations are transparently handled by the storage backend:

- ✅ File uploads
- ✅ File downloads  
- ✅ File deletion
- ✅ Directory management
- ✅ File existence checks
- ✅ File metadata retrieval
- ✅ Temporary query file cleanup
- ✅ User directory management

### Key Features

1. **Automatic Backend Selection**: The system automatically chooses the right backend based on `STORAGE_TYPE`
2. **Transparent Operation**: Existing code works without changes
3. **Error Handling**: Comprehensive error handling and logging
4. **Bucket Management**: Automatic S3 bucket creation if it doesn't exist
5. **Path Normalization**: Consistent path handling across backends

## Migration Between Storage Types

### From Local to S3

1. Stop the application
2. Update environment variables to use S3
3. Optionally migrate existing files:
   ```bash
   # Using AWS CLI (for AWS S3)
   aws s3 sync ./tmp/uploads/ s3://your-bucket/
   
   # Using MinIO Client (for MinIO)
   mc alias set myminio http://localhost:9000 minioadmin minioadmin
   mc cp --recursive ./tmp/uploads/ myminio/smse-files/
   ```
4. Start the application

### From S3 to Local

1. Stop the application
2. Download files from S3:
   ```bash
   # Using AWS CLI
   aws s3 sync s3://your-bucket/ ./tmp/uploads/
   
   # Using MinIO Client
   mc cp --recursive myminio/smse-files/ ./tmp/uploads/
   ```
3. Update environment variables to use local storage
4. Start the application

## Monitoring and Maintenance

### MinIO Health Check

The docker-compose includes a health check for MinIO:
```bash
docker compose ps  # Check service status
```

### Storage Usage

Monitor storage usage through:
- **MinIO Console**: http://localhost:9001
- **Application Logs**: File operation logs
- **API Endpoints**: Existing file management endpoints

### Backup Strategies

#### Local Storage
```bash
# Simple backup
tar -czf backup-$(date +%Y%m%d).tar.gz tmp/uploads/
```

#### S3 Storage
```bash
# Using MinIO Client
mc mirror myminio/smse-files/ ./backup/

# Using AWS CLI  
aws s3 sync s3://your-bucket/ ./backup/
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if MinIO is running on the correct port
2. **Access Denied**: Verify credentials and bucket permissions
3. **Bucket Not Found**: The system will try to create it automatically
4. **SSL Issues**: Set `S3_USE_SSL=false` for local MinIO

### Debug Mode

Enable debug logging in your Flask configuration:
```python
LOGGING = {
    'level': 'DEBUG',
    'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
}
```

### Testing Storage Backend

You can test the storage backend with a simple script:
```python
from smse_backend.services.file_storage import file_storage
from flask import Flask

app = Flask(__name__)
app.config.from_object('smse_backend.config.development.DevelopmentConfig')

with app.app_context():
    # Test file operations
    print(f"Storage type: {app.config.get('STORAGE_TYPE')}")
    print(f"Backend: {type(file_storage.backend).__name__}")
```

## Performance Considerations

### Local Storage
- **Pros**: Fast, no network overhead, simple setup
- **Cons**: Limited scalability, single point of failure, no redundancy

### S3 Storage  
- **Pros**: Scalable, redundant, can handle large files, distributed access
- **Cons**: Network latency, requires internet for AWS S3, additional complexity

### Recommendations

- **Development**: Use local storage for simplicity
- **Production**: Use S3-compatible storage for scalability and reliability
- **Self-hosted**: MinIO provides excellent S3 compatibility with full control
