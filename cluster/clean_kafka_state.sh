rm -rf ./tmp/zookeeper-data/*
rm -rf ./tmp/zookeeper-logs/*
rm -rf ./tmp/kafka-logs/*
rm -f ./zookeeper_latest.sif
rm -f ./kafka-broker.txt
rm -f ./task_manager.txt
rm -f ./worker_*

echo "Cleaning Singularity cache..."
singularity cache clean

echo "Stopping and removing instances..."
singularity instance stop --all
singularity instance clean
