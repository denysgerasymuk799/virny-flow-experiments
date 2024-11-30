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
    --bind ./tmp/zookeeper-data:/opt/bitnami/zookeeper/data \
    --bind ./tmp/zookeeper-logs:/opt/bitnami/zookeeper/logs \
    --bind ./tmp/zookeeper-data/zoo.cfg:/opt/bitnami/zookeeper/conf/zoo.cfg \
    $ZOOKEEPER_IMAGE \
    sh -c "ALLOW_ANONYMOUS_LOGIN=yes && /opt/bitnami/zookeeper/bin/zkServer.sh start" > /dev/null 2>&1 &

# Wait for Zookeeper to start
echo "Waiting for Zookeeper to initialize..."
sleep 20

# Step 2: Start Kafka Broker
echo "Starting Kafka Broker..."
singularity exec \
    --bind ./tmp/kafka-data:/opt/bitnami/kafka/data \
    --bind ./tmp/kafka-logs:/opt/bitnami/kafka/logs \
    $KAFKA_IMAGE \
    sh -c "/opt/bitnami/kafka/bin/kafka-server-start.sh /opt/bitnami/kafka/config/server.properties.original" > /dev/null 2>&1 &

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
      echo -e '\nSuccessfully created the following topics:' && \
      kafka-topics --bootstrap-server localhost:$KAFKA_PORT1 --list
    "

echo "Kafka setup completed successfully!"
