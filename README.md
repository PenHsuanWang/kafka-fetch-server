# Kafka Fetcher Server

The Kafka Fetcher Server is developed using FastAPI, providing a robust and efficient Kafka Consumer Management Service through a RESTful API. This service is specifically designed to streamline the creation, management, and monitoring of Kafka consumers and consumer groups, making it easier for developers to handle the complexities of messaging systems. By allowing users to establish and customize their own consumers, the Kafka Fetcher Server enhances the efficiency of message fetching from Kafka clusters. This capability ensures that data is processed systematically and promptly, which is critical for real-time applications.

---

## **1. Overview**

The Kafka Fetcher Server provides a comprehensive solution for dynamically managing Kafka consumers. With this service, users (or other services/UI clients) can:

1. **Create, Start, Stop, and Delete Kafka Consumers:**

   - **Create Consumers:** Define new Kafka consumers with specific configurations such as broker details, topics, consumer groups, and assign custom downstream processors.
   - **Start Consumers:** Activate consumers to begin processing messages from Kafka topics.
   - **Stop Consumers:** Deactivate consumers to halt message processing without deleting configurations.
   - **Delete Consumers:** Permanently remove consumers and their configurations from the system.

2. **Configure Downstream Processors:**

   - Attach multiple processors to consumers to handle messages in various ways.
   - **Processor Types Include:**
     - **File Sink Processor:** Write messages to local or network-mounted files.
     - **Database Sync Processor:** Insert messages into databases like PostgreSQL.
     - **Streaming Forwarder Processor:** Forward messages to external APIs via HTTP requests.
   - **Extensibility:** Easily add new processor types by implementing the `BaseProcessor` interface.

3. **Monitor Consumer Status and Metrics:**

   - **Status Tracking:** Check the current status of consumers (e.g., `ACTIVE`, `INACTIVE`, `ERROR`).
   - **Metrics Collection:** Gather consumption rates, error counts, and lag metrics for monitoring.
   - **Health Checks:** Ensure consumers and processors are operating as expected.

4. **Query Committed Offsets and Lag:**

   - **Committed Offsets:** Retrieve the last committed offsets for consumer groups.
   - **Lag Details:** Obtain current offsets, log-end offsets, and calculate lag for each partition within a topic.

These capabilities enable you to:

- **Dynamically manage** Kafka consumers without manual intervention.
- **Customize message processing** by attaching various downstream processors.
- **Ensure reliability and scalability** in message consumption and processing.
- **Quickly diagnose** how far behind a consumer group may be.
- **Integrate with dashboards** or other monitoring tools to visualize consumer lag in real time.

By abstracting the complexities involved in Kafka consumer management and providing a flexible architecture, the Kafka Fetcher Server allows you to focus on building applications without worrying about the underlying messaging infrastructure.

---

## **2. How to Run**

### **2.1. Prerequisites**

- **Python 3.9+**: Ensure Python is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
- **Kafka Cluster**: Have access to a Kafka cluster. This could be a local setup using Docker or a managed service like Confluent Cloud.
- **PostgreSQL Database**: For persisting consumer and processor configurations.
- **Environment Variables**: Configure the necessary environment variables for database connections, Kafka broker addresses, and other settings.

### **2.2. Installation**

1. **Clone the Repository**
    ```bash
    git clone https://github.com/PenHsuanWang/kafka-fetch-server.git
    cd kafka-fetch-server
    ```

2. **Set Up Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables**
    - Create a `.env` file in the project root or set environment variables directly.
    - Example `.env`:
      ```
      DATABASE_URL=postgresql://user:password@localhost:5432/kafka_fetcher
      KAFKA_BOOTSTRAP_SERVERS=localhost:9092
      LOG_LEVEL=INFO
      ```

### **2.3. Running the Server**

1. **Start the Server**
    ```bash
    python run_server.py
    ```
    - By default, the FastAPI server will run on [http://0.0.0.0:8000](http://0.0.0.0:8000).

2. **Access API Documentation**
    - Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI documentation.

---

## **3. API Endpoints**

Below are the **consumer management** and **monitoring** endpoints exposed by the Kafka Fetcher Server.

### **3.1. Consumer Management Endpoints**

#### **3.1.1. Create a Consumer**

**Endpoint**:
```
POST /api/consumers
```

**Description**:
Creates a Kafka consumer with specified configurations and (optionally) starts it immediately.

**Request Body**:
```json
{
  "broker_ip": "192.168.0.10",
  "broker_port": 9092,
  "topic": "payments",
  "consumer_group": "payment_group",
  "auto_start": true,
  "processor_configs": [
    {
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      }
    },
    {
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:password@db-host/payments"
      }
    }
  ]
}
```

**Response**:
```json
{
  "consumer_id": "uuid-string",
  "broker_ip": "192.168.0.10",
  "broker_port": 9092,
  "topic": "payments",
  "consumer_group": "payment_group",
  "status": "ACTIVE",
  "processor_configs": [
    {
      "id": "uuid-string",
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    },
    {
      "id": "uuid-string",
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:password@db-host/payments"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

#### **3.1.2. Get a Consumer**

**Endpoint**:
```
GET /api/consumers/{consumer_id}
```

**Description**:
Fetches the **full details** of the specified consumer.

**Response**:
```json
{
  "consumer_id": "uuid-string",
  "broker_ip": "192.168.0.10",
  "broker_port": 9092,
  "topic": "payments",
  "consumer_group": "payment_group",
  "status": "ACTIVE",
  "processor_configs": [
    {
      "id": "uuid-string",
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    },
    {
      "id": "uuid-string",
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:password@db-host/payments"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

#### **3.1.3. Start a Consumer**

**Endpoint**:
```
POST /api/consumers/{consumer_id}/start
```

**Description**:
Manually starts a **stopped** consumer.

**Response**:
```json
{
  "consumer_id": "uuid-string",
  "status": "ACTIVE"
}
```

#### **3.1.4. Stop a Consumer**

**Endpoint**:
```
POST /api/consumers/{consumer_id}/stop
```

**Description**:
Stops an **active** consumer.

**Response**:
```json
{
  "consumer_id": "uuid-string",
  "status": "INACTIVE"
}
```

#### **3.1.5. Update a Consumer**

**Endpoint**:
```
PUT /api/consumers/{consumer_id}
```

**Description**:
Updates consumer details (broker, topic, group, or changes downstream processors).

**Request Body**:
```json
{
  "broker_ip": "new-broker-ip",
  "broker_port": 9093,
  "topic": "new_topic",
  "processor_configs": [
    {
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:pwd@host/db"
      }
    }
  ]
}
```

**Response**:
```json
{
  "consumer_id": "uuid-string",
  "broker_ip": "new-broker-ip",
  "broker_port": 9093,
  "topic": "new_topic",
  "consumer_group": "payment_group",
  "status": "INACTIVE",
  "processor_configs": [
    {
      "id": "uuid-string",
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:pwd@host/db"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-02T09:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-02T09:00:00Z"
}
```

#### **3.1.6. Delete a Consumer**

**Endpoint**:
```
DELETE /api/consumers/{consumer_id}
```

**Description**:
Permanently deletes the consumer. If it’s active, it will be stopped first.

**Response**:
- **204 No Content** (successful deletion)

### **3.2. Monitoring Endpoints**

#### **3.2.1. Get Consumer Group Offsets**

**Endpoint**:
```
GET /monitor/consumer-group-offsets
```

**Query Parameters**:
- **`group_id`** (required, `str`): The Kafka consumer group ID you want to inspect.
- **`bootstrap_servers`** (optional, `str`): The Kafka bootstrap server(s) to connect to. Defaults to `localhost:9092`.

**Description**:
Retrieves the **committed offsets** for all partitions (across all topics) tracked by the specified consumer group.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/monitor/consumer-group-offsets?group_id=my-consumer-group&bootstrap_servers=localhost:9092"
```

**Example Response** (JSON):
```json
{
  "my-topic": {
    "0": 42,
    "1": 109,
    "2": 87
  },
  "another-topic": {
    "0": 15
  }
}
```

#### **3.2.2. Get Consumer Group Lag (for a Specific Topic)**

**Endpoint**:
```
GET /monitor/consumer-group-lag
```

**Query Parameters**:
- **`group_id`** (required, `str`): The Kafka consumer group ID to query.
- **`topic`** (required, `str`): The topic you want to check for lag.
- **`bootstrap_servers`** (optional, `str`): Defaults to `localhost:9092`.

**Description**:
Fetches the **current offset**, the **log-end offset**, and **lag** (difference) for each partition **in a single topic**, from the perspective of a given consumer group.

**Example Request**:
```bash
curl -X GET "http://localhost:8000/monitor/consumer-group-lag?group_id=my-consumer-group&topic=my-topic&bootstrap_servers=localhost:9092"
```

**Example Response** (JSON):
```json
{
  "0": {
    "current_offset": 42,
    "log_end_offset": 45,
    "lag": 3
  },
  "1": {
    "current_offset": 109,
    "log_end_offset": 109,
    "lag": 0
  },
  "2": {
    "current_offset": 87,
    "log_end_offset": 92,
    "lag": 5
  }
}
```

---

## **4. Configuration**

### **4.1. Environment Variables**

The Kafka Fetcher Server uses the following environment variables for configuration:

- **`DATABASE_URL`**: PostgreSQL connection string.
  - Example: `postgresql://user:password@localhost:5432/kafka_fetcher`
- **`KAFKA_BOOTSTRAP_SERVERS`**: Kafka broker addresses.
  - Example: `localhost:9092`
- **`LOG_LEVEL`**: Logging level (e.g., `INFO`, `DEBUG`, `ERROR`).
  - Default: `INFO`

### **4.2. Config Files**

Configuration settings are managed using Pydantic's `BaseSettings` in `app/config/settings.py`. This allows for centralized and type-safe configuration management.

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## **5. Example Usage**

### **5.1. Creating a Consumer**

**Request**:
```bash
curl -X POST "http://localhost:8000/api/consumers" \
     -H "Content-Type: application/json" \
     -d '{
           "broker_ip": "192.168.0.10",
           "broker_port": 9092,
           "topic": "payments",
           "consumer_group": "payment_group",
           "auto_start": true,
           "processor_configs": [
             {
               "processor_type": "file_sink",
               "config": {
                 "file_path": "/var/log/payment_messages.log"
               }
             },
             {
               "processor_type": "database_sync",
               "config": {
                 "db_dsn": "postgresql://user:password@db-host/payments"
               }
             }
           ]
         }'
```

**Response**:
```json
{
  "consumer_id": "123e4567-e89b-12d3-a456-426614174000",
  "broker_ip": "192.168.0.10",
  "broker_port": 9092,
  "topic": "payments",
  "consumer_group": "payment_group",
  "status": "ACTIVE",
  "processor_configs": [
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    },
    {
      "id": "323e4567-e89b-12d3-a456-426614174002",
      "processor_type": "database_sync",
      "config": {
        "db_dsn": "postgresql://user:password@db-host/payments"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

### **5.2. Monitoring Consumer Lag**

**Request**:
```bash
curl -X GET "http://localhost:8000/monitor/consumer-group-lag?group_id=payment_group&topic=payments&bootstrap_servers=localhost:9092"
```

**Response**:
```json
{
  "0": {
    "current_offset": 42,
    "log_end_offset": 45,
    "lag": 3
  },
  "1": {
    "current_offset": 109,
    "log_end_offset": 109,
    "lag": 0
  },
  "2": {
    "current_offset": 87,
    "log_end_offset": 92,
    "lag": 5
  }
}
```

---

## **6. Testing**

### **6.1. Unit Tests**

Run unit tests to verify individual components.

```bash
pytest tests/unit/
```

### **6.2. Integration Tests**

Run integration tests to validate interactions between components.

```bash
pytest tests/integration/
```

### **6.3. Load Tests**

Assess the system's performance under high load using tools like Locust or k6.

```bash
# Example using Locust
locust -f tests/load_tests/locustfile.py
```

---

## **7. Deployment**

### **7.1. Containerization with Docker**

1. **Build the Docker Image**
    ```bash
    docker build -t kafka-fetcher-server:latest .
    ```

2. **Run the Docker Container**
    ```bash
    docker run -d \
           --name kafka-fetcher-server \
           -p 8000:8000 \
           -e DATABASE_URL=postgresql://user:password@db-host:5432/kafka_fetcher \
           -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
           -e LOG_LEVEL=INFO \
           kafka-fetcher-server:latest
    ```

### **7.2. Orchestration with Kubernetes**

Deploying the Kafka Fetcher Server using Kubernetes involves creating Deployment and Service manifests.

1. **Create Deployment Manifest (`deployment.yaml`)**
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: kafka-fetcher-server
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: kafka-fetcher-server
      template:
        metadata:
          labels:
            app: kafka-fetcher-server
        spec:
          containers:
          - name: kafka-fetcher-server
            image: kafka-fetcher-server:latest
            ports:
            - containerPort: 8000
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: kafka-fetcher-secrets
                  key: DATABASE_URL
            - name: KAFKA_BOOTSTRAP_SERVERS
              value: "localhost:9092"
            - name: LOG_LEVEL
              value: "INFO"
    ```

2. **Create Service Manifest (`service.yaml`)**
    ```yaml
    apiVersion: v1
    kind: Service
    metadata:
      name: kafka-fetcher-server-service
    spec:
      type: LoadBalancer
      ports:
      - port: 80
        targetPort: 8000
      selector:
        app: kafka-fetcher-server
    ```

3. **Apply Manifests**
    ```bash
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
    ```

### **7.3. Managing Secrets**

Use Kubernetes Secrets or a secrets manager like HashiCorp Vault to manage sensitive information.

**Example: Creating a Secret**
```bash
kubectl create secret generic kafka-fetcher-secrets \
    --from-literal=DATABASE_URL='postgresql://user:password@db-host:5432/kafka_fetcher'
```

---

## **8. Contributing**

Contributions are welcome! Please follow these steps to contribute:

1. **Fork the Repository**

2. **Create a Feature Branch**
    ```bash
    git checkout -b feature/your-feature-name
    ```

3. **Commit Your Changes**
    ```bash
    git commit -m "Add your message"
    ```

4. **Push to the Branch**
    ```bash
    git push origin feature/your-feature-name
    ```

5. **Create a Pull Request**

Please ensure that your contributions adhere to the following guidelines:

- **Code Style**: Follow PEP 8 standards.
- **Documentation**: Update the README and docstrings as necessary.
- **Testing**: Include relevant tests for new features or bug fixes.
- **Commit Messages**: Write clear and descriptive commit messages.

---

## **9. License**

This project is licensed under the [MIT License](LICENSE).

---

## **10. Contact**

For questions or feedback, please reach out to the **Kafka Consumer Management** team or open an issue in the [repository](https://github.com/PenHsuanWang/kafka-fetch-server/issues).

Enjoy managing and monitoring your Kafka consumers with the **Kafka Fetcher Server**!

---

## **11. Future Enhancements**

1. **Auto-Recovery**: Automatically restart consumers that encounter transient errors.
2. **Batching**: Support batch consumption and processing for high-throughput topics.
3. **RBAC & Multi-Tenancy**: Implement fine-grained permissions and tenant isolation.
4. **Partition-Level Control**: Provide advanced features like custom partition assignments.
5. **Versioning**: Track processor or consumer versions to allow rollback or multi-version deployments.

---

By following this comprehensive README, users and developers can effectively set up, use, and contribute to the Kafka Fetcher Server, ensuring seamless integration and efficient management of Kafka consumers and consumer groups in their environments.