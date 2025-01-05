"""Run server script.

Initializes the Singleton KafkaConsumerManager and starts the FastAPI application.
"""

import uvicorn
from server import app
from app.services.kafka_manager_service import KafkaConsumerManager


def main() -> None:
    """
    Main entry point to run the FastAPI server.

    :return: None
    :rtype: None
    """
    # Instantiate the KafkaConsumerManager (Singleton).
    manager = KafkaConsumerManager()
    # Potentially, load existing consumers from the DB or perform other startup tasks here.

    # Start the FastAPI application using Uvicorn.
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
