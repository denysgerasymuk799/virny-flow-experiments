#!/bin/bash

# Define variables
ZOOKEEPER_IMAGE="docker://bitnami/zookeeper:latest"
KAFKA_IMAGE="docker://bitnami/kafka:latest"
INIT_IMAGE="docker://confluentinc/cp-kafka:6.1.1"

ZOOKEEPER_PORT=2181
KAFKA_PORT1=9092
KAFKA_PORT2=9093

# Step 1: Start Zookeeper
echo "Starting Zookeeper..."
singularity exec \
    --bind /tmp/zookeeper-data:/zookeeper-data \
    $ZOOKEEPER_IMAGE \
    sh -c "ALLOW_ANONYMOUS_LOGIN=yes && zookeeper-server-start.sh" &

# Wait for Zookeeper to start
echo "Waiting for Zookeeper to initialize..."
sleep 20

# Step 2: Start Kafka Broker
echo "Starting Kafka Broker..."
singularity exec \
    --bind /tmp/kafka-data:/kafka-data \
    $KAFKA_IMAGE \
    sh -c "KAFKA_CFG_BROKER_ID=1 \
           KAFKA_CFG_ZOOKEEPER_CONNECT=localhost:$ZOOKEEPER_PORT \
           KAFKA_CFG_LISTENERS=PLAINTEXT_INTERNAL://0.0.0.0:$KAFKA_PORT1,PLAINTEXT_EXTERNAL://0.0.0.0:$KAFKA_PORT2 \
           KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT_INTERNAL://kafka_broker:$KAFKA_PORT1,PLAINTEXT_EXTERNAL://localhost:$KAFKA_PORT2 \
           KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT_INTERNAL:PLAINTEXT,PLAINTEXT_EXTERNAL:PLAINTEXT \
           KAFKA_CFG_INTER_BROKER_LISTENER_NAME=PLAINTEXT_INTERNAL \
           KAFKA_CFG_GROUP_MIN_SESSION_TIMEOUT_MS=6000 \
           KAFKA_CFG_GROUP_MAX_SESSION_TIMEOUT_MS=60000 \
           ALLOW_PLAINTEXT_LISTENER=yes && kafka-server-start.sh" &

# Wait for Kafka to start
echo "Waiting for Kafka Broker to initialize..."
sleep 30

# Step 3: Initialize Kafka Topics
echo "Initializing Kafka Topics..."
singularity exec \
    $INIT_IMAGE \
    sh -c "
      kafka-topics --bootstrap-server localhost:$KAFKA_PORT1 --list && \
      kafka-topics --bootstrap-server localhost:$KAFKA_PORT1 --create --if-not-exists --topic NewTasksQueue --replication-factor 1 --partitions 10 && \
      kafka-topics --bootstrap-server localhost:$KAFKA_PORT1 --create --if-not-exists --topic CompletedTasksQueue --replication-factor 1 --partitions 10 && \
      kafka-topics --bootstrap-server localhost:$KAFKA_PORT1 --list
    "

echo "Kafka setup completed successfully!"
