kill $(lsof -ti:8080,8081,8082,8083,7000,7001,7002,7003)

python3 apps/fabric/src/server/start_server.py 0 &> apps/fabric/log/log_0.txt &
python3 apps/fabric/src/server/start_server.py 1 &> apps/fabric/log/log_1.txt &
python3 apps/fabric/src/server/start_server.py 2 &> apps/fabric/log/log_2.txt &
python3 apps/fabric/src/server/start_server.py 3 &> apps/fabric/log/log_3.txt &

sleep 2

python3 apps/fabric/src/client/start_client.py