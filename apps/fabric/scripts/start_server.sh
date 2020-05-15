echo "peer0.org1.example.com "
docker exec peer0.org1.example.com /bin/bash \
  -c 'cd /usr/src/HoneyBadgerMPC && python3.7 apps/fabric/src/server/start_server.py 0 &> apps/fabric/log/log_0.txt' &

echo "peer1.org1.example.com"
docker exec peer1.org1.example.com /bin/bash \
  -c 'cd /usr/src/HoneyBadgerMPC && python3.7 apps/fabric/src/server/start_server.py 1 &> apps/fabric/log/log_1.txt' &

echo "peer0.org2.example.com"
docker exec peer0.org2.example.com /bin/bash \
  -c 'cd /usr/src/HoneyBadgerMPC && python3.7 apps/fabric/src/server/start_server.py 2 &> apps/fabric/log/log_2.txt' &

echo "peer1.org2.example.com"
docker exec peer1.org2.example.com /bin/bash \
  -c 'cd /usr/src/HoneyBadgerMPC && python3.7 apps/fabric/src/server/start_server.py 3 &> apps/fabric/log/log_3.txt' &