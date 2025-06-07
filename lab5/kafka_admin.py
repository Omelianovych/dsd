from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import time

BOOTSTRAP_SERVERS = ["localhost:9092", "localhost:9093", "localhost:9094"]
TOPIC_NAME = "messages"
NUM_PARTITIONS = 2
REPLICATION_FACTOR = 3

def main():
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            client_id="topic-manager"
        )
        print("Kafka AdminClient connected successfully.")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return

    new_topic = NewTopic(
        name=TOPIC_NAME,
        num_partitions=NUM_PARTITIONS,
        replication_factor=REPLICATION_FACTOR
    )

    try:
        admin.create_topics([new_topic])
        print(f"Topic '{TOPIC_NAME}' created successfully.")
    except TopicAlreadyExistsError:
        print(f"Topic '{TOPIC_NAME}' already exists. No action taken.")
    except Exception as e:
        print(f"Failed to create topic '{TOPIC_NAME}': {e}")
    finally:
        admin.close()

if __name__ == "__main__":
    # Даем брокерам время на запуск
    print("Waiting for Kafka brokers to be ready...")
    time.sleep(10)
    main()