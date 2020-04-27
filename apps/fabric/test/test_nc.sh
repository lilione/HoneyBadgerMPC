python3 apps/fabric/start_server.py 0 &> apps/fabric/test/log/log_0.txt &
python3 apps/fabric/start_server.py 1 &> apps/fabric/test/log/log_1.txt &
python3 apps/fabric/start_server.py 2 &> apps/fabric/test/log/log_2.txt &
python3 apps/fabric/start_server.py 3 &> apps/fabric/test/log/log_3.txt &

python3 apps/fabric/test/test_client.py