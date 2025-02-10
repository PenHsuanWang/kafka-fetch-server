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

![high-jevel-conceptual-diagram](https://hackmd.io/_uploads/B1Y8mQOL1g.png)

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

Below are the **consumer management** and **monitoring** endpoints exposed by the Kafka Fetcher Server. These endpoints allow users to create, manage, and monitor Kafka consumers efficiently.

### **3.1. Consumer Management Endpoints**

#### **3.1.1. List All Consumers**

**Endpoint**:
```
GET /consumers/
```

**Description**:  
Retrieves a list of all Kafka consumers currently managed in memory.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumers/" \
     -H "Accept: application/json"
```

**Expected Response** (`200 OK`):
```json
[
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
      }
    ],
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-01T12:00:00Z"
  }
]
```

---

#### **3.1.2. Create a Consumer**

**Endpoint**:
```
POST /consumers/
```

**Description**:  
Creates a new Kafka consumer with specified configurations and (optionally) starts it immediately.

**Request Body**:

The payload must adhere to the following structure:

- **`broker_ip`** (`str`, **required**): The IP address of the Kafka broker.
- **`broker_port`** (`int`, **required**): The port number of the Kafka broker.
- **`topic`** (`str`, **required**): The Kafka topic to consume from.
- **`consumer_group`** (`str`, **required**): The consumer group ID.
- **`auto_start`** (`bool`, **required**): Determines whether the consumer should start immediately upon creation.
- **`processor_configs`** (`list`, **required**): A list of downstream processor configurations.

Each **processor configuration** within `processor_configs` must include:

- **`processor_type`** (`str`, **required**): The type of processor (`file_sink`).
- **`config`** (`dict`, **required**): A dictionary containing configuration parameters specific to the processor type.

**Simplified Example Using Only `file_sink` Processor**:

To minimize dependencies and simplify the setup, configure the consumer with only the `file_sink` processor. This avoids the need for additional services like PostgreSQL.

**Example `curl` Command**:
```bash
curl -X POST "http://localhost:8000/consumers/" \
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
             }
           ]
         }'
```

**Expected Response** (`201 Created`):
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
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

**Notes**:
- The `consumer_id` is a UUID generated by the server.
- The `status` field reflects whether the consumer is `ACTIVE` or `INACTIVE`.
- `processor_configs` includes detailed configurations for each downstream processor, each with its own unique `id`.
- By using only `file_sink`, you eliminate the need for setting up a database, making the quick start easier.

---

#### **3.1.3. Get a Consumer**

**Endpoint**:
```
GET /consumers/{consumer_id}
```

**Description**:  
Fetches the **full details** of the specified consumer.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to retrieve.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000" \
     -H "Accept: application/json"
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`200 OK`):
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
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Consumer 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

#### **3.1.4. Start a Consumer**

**Endpoint**:
```
POST /consumers/{consumer_id}/start
```

**Description**:  
Manually starts a **stopped** consumer.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to start.

**Example `curl` Command**:
```bash
curl -X POST "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000/start" \
     -H "Accept: application/json"
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`200 OK`):
```json
{
  "consumer_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "ACTIVE"
}
```

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Consumer 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

#### **3.1.5. Stop a Consumer**

**Endpoint**:
```
POST /consumers/{consumer_id}/stop
```

**Description**:  
Stops an **active** consumer.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to stop.

**Example `curl` Command**:
```bash
curl -X POST "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000/stop" \
     -H "Accept: application/json"
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`200 OK`):
```json
{
  "consumer_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "INACTIVE"
}
```

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Consumer 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

#### **3.1.6. Update a Consumer**

**Endpoint**:
```
PUT /consumers/{consumer_id}
```

**Description**:  
Updates consumer details such as broker IP, broker port, topic, or processor configurations.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to update.

**Request Body**:
You can include any combination of the following fields to update:

- **`broker_ip`** (`str`, *optional*): The new IP address of the Kafka broker.
- **`broker_port`** (`int`, *optional*): The new port number of the Kafka broker.
- **`topic`** (`str`, *optional*): The new Kafka topic to consume from.
- **`consumer_group`** (`str`, *optional*): The new consumer group ID.
- **`processor_configs`** (`list`, *optional*): A new list of downstream processor configurations.

**Simplified Example Updating Only Broker IP and Port**:

To keep things simple and avoid adding more dependencies, update only the broker details without altering processor configurations.

**Example `curl` Command**:
```bash
curl -X PUT "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000" \
     -H "Content-Type: application/json" \
     -d '{
           "broker_ip": "192.168.0.20",
           "broker_port": 9094
         }'
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`200 OK`):
```json
{
  "consumer_id": "123e4567-e89b-12d3-a456-426614174000",
  "broker_ip": "192.168.0.20",
  "broker_port": 9094,
  "topic": "payments",
  "consumer_group": "payment_group",
  "status": "INACTIVE",
  "processor_configs": [
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-03T10:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-03T10:00:00Z"
}
```

**Notes**:
- If you choose to update `processor_configs`, ensure that the new configurations are complete. Existing processors not included in the new list will be removed.
- Since we're focusing on minimizing dependencies, sticking with the `file_sink` processor ensures that you don't need to set up a database.

---

#### **3.1.7. Delete a Consumer**

**Endpoint**:
```
DELETE /consumers/{consumer_id}
```

**Description**:  
Permanently deletes the consumer. If it’s active, it will be stopped first.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to delete.

**Example `curl` Command**:
```bash
curl -X DELETE "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000" \
     -H "Accept: application/json"
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`204 No Content`):
- **Body**: *(No content)*

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Consumer 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

## 3.2. Consumer Group Monitoring Endpoints

In addition to managing individual consumers, the Kafka Fetcher Server provides endpoints to **monitor consumer groups**. These allow you to **list** available groups and **fetch offset details** (e.g., committed offsets) for a particular group.

### 3.2.1. List Consumer Groups

**Endpoint**:
```
GET /consumergroups/
```

**Description**:  
Returns a list of **Kafka consumer group IDs**. By default, it lists only the **consumer groups** recognized by this service (i.e., groups that you have created via this system). You can optionally specify a **query parameter** to list **all** consumer groups known to the Kafka cluster.

**Query Parameter**:
- **`all_groups`** (`bool`, *optional*; default: `false`):  
  - **`true`** → Lists *all* consumer groups in the Kafka cluster.  
  - **`false`** → Lists only consumer groups that this server created/knows about.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumergroups?all_groups=true"
```

**Expected Response** (`200 OK`):
```json
{
  "consumer_groups": [
    "payment_group",
    "order_group",
    "inventory_group"
  ]
}
```

If the server has **no** local groups and `all_groups=false`, you might see:
```json
{
  "consumer_groups": []
}
```

---

### 3.2.2. Get Consumer Group Offsets

**Endpoint**:
```
GET /consumergroups/{group_id}/offsets
```

**Description**:  
Retrieves **offset details** for a specified consumer group, including the **topic**, **partition**, and **current committed offset** for each partition that the group consumes. If the group does not exist or has no committed offsets, you receive **404 Not Found**.

**Path Parameter**:
- **`group_id`** (`str`, **required**): The consumer group ID to inspect.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumergroups/payment_group/offsets"
```

**Expected Response** (`200 OK`):
```json
{
  "group_id": "payment_group",
  "offsets": [
    {
      "topic": "payments",
      "partition": 0,
      "current_offset": 42,
      "metadata": null
    },
    {
      "topic": "payments",
      "partition": 1,
      "current_offset": 109,
      "metadata": ""
    }
  ]
}
```

**Error Response** (`404 Not Found`):
```json
{
  "detail": "Consumer group 'some_unknown_group' not found or no offsets committed."
}
```

---

### Example Usage

1. **List All Groups** in the cluster:
   ```bash
   curl -X GET "http://localhost:8000/consumergroups?all_groups=true"
   ```
   This returns **every** consumer group that Kafka knows about, not just the ones managed by this server.

2. **List Only Groups** known to this service:
   ```bash
   curl -X GET "http://localhost:8000/consumergroups"
   ```
   Returns consumer groups that the **Kafka Fetcher Server** has created in memory.

3. **Get Offsets** for a specific group:
   ```bash
   curl -X GET "http://localhost:8000/consumergroups/payment_group/offsets"
   ```
   Provides an array of partition offsets (and optional metadata) for `payment_group`.

With these **consumer group monitoring** endpoints, you can programmatically track **which consumer groups exist**, verify **where they are reading**, and **monitor** if they have **committed offsets** as expected.

---

### **3.3. Additional Testing Examples**

To further assist you in testing the API endpoints, here are some additional `curl` commands that cover various scenarios:

#### **3.3.1. Error Handling Example**

**Scenario**:  
Attempting to retrieve a consumer that does not exist.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumers/non-existent-uuid" \
     -H "Accept: application/json"
```

**Expected Response** (`404 Not Found`):
```json
{
  "detail": "Consumer non-existent-uuid not found"
}
```

---

#### **3.3.2. Update a Consumer Without Processor Configurations**

**Endpoint**:
```
PUT /consumers/{consumer_id}
```

**Description**:  
Updates only the broker IP and port without altering processor configurations.

**Path Parameter**:
- **`consumer_id`** (`str`, **required**): The UUID of the consumer to update.

**Request Body**:
```json
{
  "broker_ip": "192.168.0.20",
  "broker_port": 9094
}
```

**Example `curl` Command**:
```bash
curl -X PUT "http://localhost:8000/consumers/123e4567-e89b-12d3-a456-426614174000" \
     -H "Content-Type: application/json" \
     -d '{
           "broker_ip": "192.168.0.20",
           "broker_port": 9094
         }'
```
*Replace `123e4567-e89b-12d3-a456-426614174000` with your actual `consumer_id`.*

**Expected Response** (`200 OK`):
```json
{
  "consumer_id": "123e4567-e89b-12d3-a456-426614174000",
  "broker_ip": "192.168.0.20",
  "broker_port": 9094,
  "topic": "payments",
  "consumer_group": "payment_group",
  "status": "INACTIVE",
  "processor_configs": [
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "processor_type": "file_sink",
      "config": {
        "file_path": "/var/log/payment_messages.log"
      },
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-03T10:00:00Z"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-03T10:00:00Z"
}
```

**Notes**:
- Since we're not altering `processor_configs`, the existing `file_sink` processor remains unchanged.
- The consumer status is updated to `INACTIVE` as a result of the broker changes.

---

### **3.4. Automated Testing with a Shell Script**

To streamline the testing process, you can create a **shell script** that sequentially tests all API endpoints. Below is an example script named `test_api_endpoints.sh`:

```bash
#!/bin/bash

# Ensure jq is installed for JSON parsing
if ! command -v jq &> /dev/null
then
    echo "jq could not be found. Please install it to run this script."
    exit
fi

BASE_URL="http://localhost:8000/consumers"

echo "=== Creating a new consumer ==="
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/" \
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
             }
           ]
         }')

echo "Response:"
echo $CREATE_RESPONSE | jq

# Extract consumer_id from the response
CONSUMER_ID=$(echo $CREATE_RESPONSE | jq -r '.consumer_id')

if [ "$CONSUMER_ID" == "null" ] || [ -z "$CONSUMER_ID" ]; then
    echo "Failed to create consumer."
    exit 1
fi

echo "Created Consumer ID: $CONSUMER_ID"

echo "=== Listing all consumers ==="
curl -s -X GET "$BASE_URL/" \
     -H "Accept: application/json" | jq
echo ""

echo "=== Getting details of the created consumer ==="
curl -s -X GET "$BASE_URL/$CONSUMER_ID" \
     -H "Accept: application/json" | jq
echo ""

echo "=== Updating the consumer's broker IP and port ==="
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/$CONSUMER_ID" \
     -H "Content-Type: application/json" \
     -d '{
           "broker_ip": "192.168.0.20",
           "broker_port": 9094
         }')

echo "Response:"
echo $UPDATE_RESPONSE | jq
echo ""

echo "=== Stopping the consumer ==="
STOP_RESPONSE=$(curl -s -X POST "$BASE_URL/$CONSUMER_ID/stop" \
     -H "Accept: application/json")

echo "Response:"
echo $STOP_RESPONSE | jq
echo ""

echo "=== Starting the consumer ==="
START_RESPONSE=$(curl -s -X POST "$BASE_URL/$CONSUMER_ID/start" \
     -H "Accept: application/json")

echo "Response:"
echo $START_RESPONSE | jq
echo ""

echo "=== Deleting the consumer ==="
DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/$CONSUMER_ID" \
     -H "Accept: application/json")

echo "Response Code: $DELETE_RESPONSE"

if [ "$DELETE_RESPONSE" == "204" ]; then
    echo "Consumer deleted successfully."
else
    echo "Failed to delete consumer."
fi
```

**Steps to Use the Script**:

1. **Save the Script**:
   - Create a new file named `test_api_endpoints.sh`.
   - Paste the above script into the file.

2. **Make the Script Executable**:
    ```bash
    chmod +x test_api_endpoints.sh
    ```

3. **Install `jq` (if not already installed)**:
   - **macOS**:
     ```bash
     brew install jq
     ```
   - **Ubuntu/Linux**:
     ```bash
     sudo apt-get install jq
     ```
   - **Windows**:
     - Download from [https://stedolan.github.io/jq/download/](https://stedolan.github.io/jq/download/) and follow installation instructions.

4. **Run the Script**:
    ```bash
    ./test_api_endpoints.sh
    ```

**What the Script Does**:

- **Creates** a new consumer with only the `file_sink` processor and captures the `consumer_id`.
- **Lists** all consumers to verify creation.
- **Fetches** the details of the newly created consumer.
- **Updates** the broker IP and port of the consumer.
- **Stops** the consumer.
- **Starts** the consumer again.
- **Deletes** the consumer.
- **Outputs** the responses at each step for verification.

*Ensure you have the FastAPI server running (`python run_server.py`) before executing the script.*

---

### **3.5. Monitoring Endpoints Testing**

#### **3.5.1. Get Consumer Group Offsets**

**Endpoint**:
```
GET /monitor/consumer-group-offsets
```

**Description**:  
Retrieves the **committed offsets** for all partitions (across all topics) tracked by the specified consumer group.

**Query Parameters**:
- **`group_id`** (`str`, **required**): The Kafka consumer group ID you want to inspect.
- **`bootstrap_servers`** (`str`, *optional*): The Kafka bootstrap server(s) to connect to. Defaults to `localhost:9092`.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/monitor/consumer-group-offsets?group_id=payment_group&bootstrap_servers=localhost:9092" \
     -H "Accept: application/json"
```

**Expected Response** (`200 OK`) (JSON):
```json
{
  "payments": {
    "0": 42,
    "1": 109,
    "2": 87
  },
  "orders": {
    "0": 15
  }
}
```

---

#### **3.5.2. Get Consumer Group Lag for a Specific Topic**

**Endpoint**:
```
GET /monitor/consumer-group-lag
```

**Description**:  
Fetches the **current offset**, the **log-end offset**, and **lag** (difference) for each partition **in a single topic**, from the perspective of a given consumer group.

**Query Parameters**:
- **`group_id`** (`str`, **required**): The Kafka consumer group ID to query.
- **`topic`** (`str`, **required**): The topic you want to check for lag.
- **`bootstrap_servers`** (`str`, *optional*): Defaults to `localhost:9092`.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/monitor/consumer-group-lag?group_id=payment_group&topic=payments&bootstrap_servers=localhost:9092" \
     -H "Accept: application/json"
```

**Expected Response** (`200 OK`) (JSON):
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

### **3.6. Testing with JSON Files**

For more complex requests, especially those involving multiple processors or intricate configurations, using JSON files can simplify the `curl` commands.

#### **3.6.1. Create a JSON File for Consumer Creation**

**File**: `create_consumer.json`

**Content**:
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
    }
  ]
}
```
*Note*: This JSON file includes only the `file_sink` processor to keep the setup simple.

#### **3.6.2. Execute `curl` Using the JSON File**

**Command**:
```bash
curl -X POST "http://localhost:8000/consumers/" \
     -H "Content-Type: application/json" \
     -d @create_consumer.json
```

**Explanation**:
- `-d @create_consumer.json`: Instructs `curl` to read the request body from the `create_consumer.json` file.

---

### **3.7. Handling Authentication and Authorization (If Applicable)**

If your API requires authentication (e.g., JWT tokens, API keys), include the necessary headers in your `curl` commands.

#### **Example with Bearer Token**

**Description**:  
Includes a JWT token in the `Authorization` header.

**Example `curl` Command**:
```bash
curl -X GET "http://localhost:8000/consumers/" \
     -H "Authorization: Bearer your_jwt_token_here" \
     -H "Accept: application/json"
```
*Replace `your_jwt_token_here` with your actual JWT token.*

**Note**:  
Ensure that your server is configured to handle authentication tokens appropriately.

---

### **3.8. Using Postman for Testing**

For a more interactive and user-friendly testing experience, consider using [Postman](https://www.postman.com/).

#### **Steps to Use Postman**

1. **Install Postman**:
   - Download and install Postman from [https://www.postman.com/downloads/](https://www.postman.com/downloads/).

2. **Create a New Collection**:
   - Open Postman and create a new collection named "Kafka Fetcher Server".

3. **Add Requests to the Collection**:
   - For each API endpoint, create a new request within the collection:
     - **Method**: Select the appropriate HTTP method (`GET`, `POST`, `PUT`, `DELETE`).
     - **URL**: Enter the full endpoint URL (e.g., `http://localhost:8000/consumers/`).
     - **Headers**: Set necessary headers (e.g., `Content-Type: application/json`, `Accept: application/json`).
     - **Body**: For `POST` and `PUT` requests, input the JSON payload in the Body tab.

4. **Example: Create a Consumer**
   - **Method**: `POST`
   - **URL**: `http://localhost:8000/consumers/`
   - **Headers**:
     - `Content-Type`: `application/json`
   - **Body**: Raw JSON as shown in the **Create a Consumer** section.
   - **Send**: Click the "Send" button to execute the request and view the response.

5. **Save and Organize Requests**:
   - Save each request with descriptive names (e.g., "Create Consumer", "List Consumers") for easy access.

6. **Execute and Test**:
   - Use Postman’s interface to execute requests, view responses, and debug as needed.

---

### **3.9. Summary of API Endpoints**

| **HTTP Method** | **Endpoint**                         | **Description**                                  |
|-----------------|--------------------------------------|--------------------------------------------------|
| `GET`           | `/consumers/`                        | List all consumers currently in memory.          |
| `POST`          | `/consumers/`                        | Create a new Kafka consumer in memory.           |
| `GET`           | `/consumers/{consumer_id}`           | Retrieve details of a specific consumer.         |
| `PUT`           | `/consumers/{consumer_id}`           | Update an existing consumer's configurations.    |
| `POST`          | `/consumers/{consumer_id}/start`     | Start a stopped Kafka consumer.                  |
| `POST`          | `/consumers/{consumer_id}/stop`      | Stop an active Kafka consumer.                   |
| `DELETE`        | `/consumers/{consumer_id}`           | Delete a Kafka consumer.                         |
| `GET`           | `/monitor/consumer-group-offsets`     | Get committed offsets for a consumer group.      |
| `GET`           | `/monitor/consumer-group-lag`         | Get lag details for a consumer group and topic.  |

**Note**:
- Replace `{consumer_id}` with the actual UUID of the consumer you intend to interact with.
- Ensure your FastAPI application is running (e.g., via `python run_server.py`) before testing these endpoints.
- Adjust the base URL (`http://localhost:8000`) as necessary based on your deployment configuration.

---

## **Consumer Statuses and Lifecycle**

In this system, each Kafka consumer is tracked with a status that reflects its current operation state. This status is returned in responses to all API calls and is used internally to manage the consumer’s behavior in the system. The following are the three key statuses:

### **1. INACTIVE**
- **Definition:**  
  The consumer exists (its configuration has been created and persisted in-memory and/or in the database) but is not actively polling messages from Kafka.
  
- **When It Occurs:**  
  - **Upon Creation:**  
    When a consumer is created via the `POST /consumers` endpoint with the flag `auto_start` set to **false**, the consumer is created in the `INACTIVE` state.
    
  - **After Stopping:**  
    When an active consumer is explicitly stopped using the `POST /consumers/{consumer_id}/stop` endpoint, its status transitions to `INACTIVE`.

- **API Example:**  
  **Create Consumer (auto_start = false)**  
  ```bash
  curl -X POST "http://localhost:8000/consumers/" \
       -H "Content-Type: application/json" \
       -d '{
             "broker_ip": "localhost",
             "broker_port": 9092,
             "topic": "payments",
             "consumer_group": "payment_group",
             "auto_start": false,
             "processor_configs": [
               {
                 "processor_type": "file_sink",
                 "config": {"file_path": "/var/log/payment_messages.log"}
               }
             ]
           }'
  ```
  **Expected Response:**  
  ```json
  {
    "consumer_id": "uuid-generated-by-server",
    "broker_ip": "localhost",
    "broker_port": 9092,
    "topic": "payments",
    "consumer_group": "payment_group",
    "status": "INACTIVE",
    "processor_configs": [ ... ],
    "created_at": "...",
    "updated_at": "..."
  }
  ```

---

### **2. ACTIVE**
- **Definition:**  
  The consumer is actively polling Kafka messages and processing them using its configured downstream processors.
  
- **When It Occurs:**  
  - **Auto-start on Creation:**  
    If the consumer is created with `auto_start` set to **true**, it immediately transitions to the `ACTIVE` state after a successful creation.
    
  - **Manual Start:**  
    When a consumer in the `INACTIVE` state is started using the `POST /consumers/{consumer_id}/start` endpoint, the consumer transitions to the `ACTIVE` state.
    
- **API Example:**  
  **Start Consumer**  
  ```bash
  curl -X POST "http://localhost:8000/consumers/{consumer_id}/start" \
       -H "Accept: application/json"
  ```
  **Expected Response:**  
  ```json
  {
    "consumer_id": "{consumer_id}",
    "status": "ACTIVE",
    ...
  }
  ```

---

### **3. ERROR**
- **Definition:**  
  The consumer has encountered a critical error—either in the Kafka consumption logic (e.g., connection failures, misconfiguration) or within one of the downstream processors—that stops it from functioning as expected.
  
- **When It Occurs:**  
  - **Runtime Exceptions:**  
    During the execution of the asynchronous message consumption loop (in `MessageExtractor._consume_loop`), if an unexpected exception occurs, the error is logged and (if configured) the consumer’s status should be updated to `ERROR`.
    
  - **Processor Failure:**  
    If a downstream processor signals a critical failure (and the design is extended to support that), the consumer’s status may be set to `ERROR`.  
    *(Note: In the current implementation, the error is logged and further handling can be added as a future enhancement, such as auto-recovery.)*
    
- **API Behavior:**  
  When a consumer is in the `ERROR` state, subsequent API calls such as `GET /consumers/{consumer_id}` will return a status of `"ERROR"`. The client (or admin) may choose to delete, reconfigure, or attempt to restart the consumer after investigating the issue.

---

### **Lifecycle Transitions**

Below is a summary of how the consumer status transitions with typical API calls:

1. **Creation:**
   - **POST /consumers**
     - **auto_start = false:** → Status is set to `INACTIVE`
     - **auto_start = true:** → The consumer immediately starts and transitions to `ACTIVE`
  
2. **Starting a Consumer:**
   - **POST /consumers/{consumer_id}/start**
     - If the consumer is `INACTIVE`, it starts consuming messages and its status is set to `ACTIVE`.
     - If the consumer is already `ACTIVE`, the call returns a status of `ACTIVE` (no duplicate start).
  
3. **Stopping a Consumer:**
   - **POST /consumers/{consumer_id}/stop**
     - If the consumer is `ACTIVE`, stopping it transitions its status to `INACTIVE`.
     - If the consumer is already `INACTIVE`, the endpoint returns the current state (`INACTIVE`).
  
4. **Error Handling:**
   - During consumption (or in processor logic), if an unrecoverable error occurs:
     - The system logs the error.
     - The consumer can be transitioned to `ERROR`, and the API will then reflect that status.
  
5. **Deletion:**
   - **DELETE /consumers/{consumer_id}**
     - If the consumer is active, it is stopped first.
     - Its record is then deleted, removing it from the system.

---

### **Detailed API Specification and Status Behavior**

#### **Consumer Management Endpoints**

- **List Consumers:**  
  - **GET /consumers/**
  - Returns all consumers with their statuses.
  
- **Create Consumer:**  
  - **POST /consumers/**
  - **Request Body Specification:**
    - `broker_ip` (string, required)
    - `broker_port` (integer, required)
    - `topic` (string, required)
    - `consumer_group` (string, required)
    - `auto_start` (boolean, required)
    - `processor_configs` (list, required) – Each item must include:
      - `processor_type` (string)
      - `config` (object with processor-specific parameters)
  - **Response:**
    - Consumer object with properties including:
      - `consumer_id` (generated UUID)
      - `status` (`ACTIVE` if auto-start is true; otherwise `INACTIVE`)
  
- **Get Consumer:**  
  - **GET /consumers/{consumer_id}**
  - Returns the current configuration and status of the consumer.
  
- **Update Consumer:**  
  - **PUT /consumers/{consumer_id}**
  - Supports partial updates. Changing processor configuration will trigger an update of the internal downstream processor list and may trigger a restart (if the consumer was active).
  
- **Start Consumer:**  
  - **POST /consumers/{consumer_id}/start**
  - Transitions the consumer from `INACTIVE` to `ACTIVE`.
  
- **Stop Consumer:**  
  - **POST /consumers/{consumer_id}/stop**
  - Transitions the consumer from `ACTIVE` to `INACTIVE`.
  
- **Delete Consumer:**  
  - **DELETE /consumers/{consumer_id}**
  - Stops (if active) and removes the consumer record; the deleted consumer is no longer retrievable.

#### **Monitoring Endpoints**

- **List Consumer Groups:**  
  - **GET /consumergroups/** – Returns the list of groups tracked by the system (optionally, all groups available in Kafka).
  
- **Get Consumer Group Offsets:**  
  - **GET /consumergroups/{group_id}/offsets**
  - Returns detailed offset information for each partition of the topics consumed by the specified group.  
  - If the consumer group does not exist or has no offsets committed, the response is a `404` error.

---

### **Example Workflow**

1. **Creating an Active Consumer:**
   - You send a POST request with `auto_start` set to `true`. The consumer is created and immediately starts consuming, returning a status of `ACTIVE`.
   
2. **Stopping an Active Consumer:**
   - When you call the stop endpoint, the consumer stops processing messages and transitions to `INACTIVE`.
   
3. **Restarting an Inactive Consumer:**
   - Sending a start request on an inactive consumer returns it to `ACTIVE` mode.
   
4. **Error Scenario:**
   - If a critical error occurs during message processing, the system will log the error, and (if configured) set the consumer’s status to `ERROR`. This lets you or an administrator know that intervention may be required.
   
5. **Deleting a Consumer:**
   - Whether active or inactive, deleting a consumer removes its configuration and stops any processing.


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