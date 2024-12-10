# kafka-fetch-server

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Server](#running-the-server)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

`kafka-fetch-server` is a robust backend server built with **FastAPI** in Python, designed to manage and monitor Kafka consumers effectively. It allows authenticated users to create **Kafka Managers** that connect to Kafka clusters, under which multiple **Kafka Consumers** can be managed. The server provides comprehensive monitoring capabilities, including health status, state tracking, offset tracking, error reporting, and performance metrics for each consumer.

## Features

- **User Management**
  - User registration and authentication using OAuth2 with JWT.
  - Secure password hashing and storage.

- **Kafka Managers**
  - Create, list, update, and delete Kafka Managers.
  - Each Kafka Manager connects to a specific Kafka cluster.

- **Kafka Consumers**
  - Create, list, and delete Kafka Consumers under specific Kafka Managers.
  - Assign consumers to specific consumer groups and topics.

- **Monitoring**
  - Real-time monitoring of consumer health status, state, offsets, errors, and performance metrics.
  - Error reporting and logging for consumer-related issues.

- **Security**
  - Authentication and authorization to ensure only authorized users can manage Kafka Managers and Consumers.
  - Role-Based Access Control (RBAC) potential for future enhancements.

- **Extensible Design**
  - Modular architecture adhering to the Open-Closed Principle.
  - Easily extendable for additional features and integrations.

## Architecture

The `kafka-fetch-server` follows a modular and layered architecture, ensuring separation of concerns and maintainability. Key components include:

- **API Routers:** Handle HTTP requests and route them to appropriate services.
- **Services:** Contain business logic for managing users, Kafka Managers, Consumers, and Monitoring.
- **Repositories:** Interface with data stores or external systems like Kafka clusters.
- **Core Components:** Include configuration management, logging, and security utilities.
- **Models:** Define data schemas for requests and responses.
- **Monitoring:** Collect and provide metrics on Kafka Consumers.

## Project Structure

```plaintext
kafka-fetch-server/
├── server.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── consumers.py
│   │       ├── kafka_managers.py
│   │       └── monitoring.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── consumer.py
│   │   ├── kafka_manager.py
│   │   └── user.py    
│   ├── services/
│   │   ├── __init__.py
│   │   ├── consumer_service.py
│   │   ├── kafka_manager_service.py
│   │   ├── monitoring_service.py
│   │   └── user_service.py 
│   └── repositories/
│       ├── __init__.py
│       ├── kafka_repository.py
│       ├── kafka_manager_repository.py
│       └── user_repository.py
├── tests/
│   ├── __init__.py
│   ├── test_consumers.py
│   ├── test_kafka_managers.py 
│   ├── test_monitoring.py
│   └── test_users.py 
├── requirements.txt
├── .gitignore
└── README.md
```

## Consumer Management Design

In the current implementation, the KafkaRepository is serving as the centralized store for Consumer objects. This repository:
 - Creates a Consumer instance using the confluent_kafka.Consumer constructor.
 - Stores the consumer reference and its associated metadata (_consumers and _consumer_metadata dictionaries).
 - Provides methods (create_consumer, get_all_consumers, get_consumers_by_manager, close_consumer, get_consumer_metadata) to manage and retrieve these consumers.

In other words, the KafkaRepository is already the “one place” in the backend that holds onto the Consumer objects. The user interface (through the REST API endpoints) interacts with this repository indirectly via the service layer, which calls KafkaRepository methods. The key flow looks like this:
1.	User Interface (Front-End):
The UI sends requests to the backend’s API routes (e.g., POST /api/v1/kafka-managers/{manager_id}/consumers/ to create a consumer).
2.	API Routes (Controller Layer):
The FastAPI routes handle authentication, request validation, and then forward requests to the service layer. For example, the create_consumer endpoint calls ConsumerService.create_consumer(...).
3.	Service Layer:
The ConsumerService contains business logic. It:
 - Validates input
 - Calls the KafkaRepository to create or manage the consumer
 - Returns domain models (e.g., ConsumerResponse) to the API routes
4.	KafkaRepository (Central Store):
The repository is where the actual Consumer object is created and stored. For example:
 - create_consumer instantiates a Consumer object and stores it in memory.
 - Other repository methods fetch or modify the Consumer instance by referencing these in-memory dictionaries.

Because all interactions with the Consumer happen through the repository, you have a single, central place that manages these objects. The UI does not directly access this repository; it interacts through HTTP endpoints that eventually lead to repository operations. This layering ensures:
 - Single Source of Truth: KafkaRepository holds the actual Consumer instances.
 - Encapsulation: The UI only knows about high-level operations (e.g., create, list, delete), not the internal details of how consumers are stored or managed.
 - Future Extendability: If you want to store consumers differently (e.g., in a database, or in a more advanced external store), you can replace the repository implementation without changing the UI or the service layer.

If you want to enhance this design further, you could:
 - Add Persistence: Instead of just storing consumers in memory, the repository could persist consumer configuration to a database. The actual running Consumer objects would still be managed in memory, but their configurations and states could be restored on restart.
 - Introduce a State Management Layer: For even more explicit state management (e.g., if scaling horizontally and needing a distributed store), adapt the repository to interact with a shared data source (like Redis or ZooKeeper).
 - Advanced UI Integration: The front-end can request, via the API, updates or reads of consumer state, and the repository remains the central, single place responsible for managing these Consumer instances.

In summary, the current approach follows the idea of having one central place (the KafkaRepository) to manage Consumer objects, maintaining a clean separation of concerns and enabling easy future modifications.

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Kafka Cluster**: Ensure you have access to a Kafka cluster.
- **Virtual Environment** (optional but recommended): Use `venv` or `virtualenv` to manage dependencies.

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/kafka-fetch-server.git
   cd kafka-fetch-server
    ```

2.	**Create and Activate Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.	**Install Dependencies**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Configuration

### 1. Environment Variables

Create a `.env` file in the root directory to store environment-specific variables. Example:

```plaintext
# app/core/config.py expects the following variables
kafka_bootstrap_servers=localhost:9092
secret_key=your-secure-secret-key
algorithm=HS256
access_token_expire_minutes=30
```


### 2. Update `app/core/config.py`

Ensure that `app/core/config.py` correctly loads these environment variables:

```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Add more configurations as needed

    class Config:
        env_file = ".env"

settings = Settings()
```


## Running the Server

Start the FastAPI server using `server.py`:

```bash
python server.py
```

## Running the Server

- **Server URL**: [http://0.0.0.0:8000](http://0.0.0.0:8000)
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

These interfaces provide detailed information about all available endpoints, request/response schemas, and allow you to interact with the API directly.

---

## Testing

The project includes a suite of unit tests to ensure the reliability and correctness of its components.

### 1. Navigate to the Project Root

```bash
cd kafka-fetch-server
```


### 2.	Run Tests Using pytest
Ensure that pytest is installed (you can add it to requirements.txt if not already present).

```bash
pip install pytest
pytest
```
This command will discover and execute all tests within the `tests/` directory.

---

## Deployment

For deploying `kafka-fetch-server` in a production environment, consider the following steps:

### 1. Containerization with Docker

Create a `Dockerfile` in the root directory:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```
### Build the Docker Image

Build the Docker image for the application:

```bash
docker build -t kafka-fetch-server .
```

### Run the Docker Container:

```bash
docker run -d -p 8000:8000 --name kafka-fetch-server kafka-fetch-server
```
### 2. Orchestration with Kubernetes

For scalability and resilience, deploy the Docker container using Kubernetes. Define Kubernetes manifests such as `Deployment` and `Service` based on your infrastructure requirements.

---

### 3. Environment Configuration

Use environment variables or Kubernetes Secrets to securely manage sensitive configurations like `SECRET_KEY`.

---

### 4. HTTPS and Security

- Serve the application behind an HTTPS-enabled proxy (e.g., Nginx, Traefik).
- Implement rate limiting and adhere to security best practices to protect the application.

---

### 5. Monitoring and Logging

Integrate monitoring tools such as Prometheus and Grafana to visualize real-time metrics and set up alerts for application performance and health.


