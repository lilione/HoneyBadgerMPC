start() {
  echo $1
  docker exec $1 /bin/bash \
  -c "cd /usr/src/HoneyBadgerMPC && python3.7 apps/fabric/src/server/start_server.py $2 &>apps/fabric/log/server/log_$2.txt" &
}

start peer0.org1.example.com 0
start peer1.org1.example.com 1
start peer0.org2.example.com 2
start peer1.org2.example.com 3