# bash apps/fabric/test/test.sh

rm apps/fabric/log/server/log_0.txt
rm apps/fabric/log/server/log_1.txt
rm apps/fabric/log/server/log_2.txt
rm apps/fabric/log/server/log_3.txt

kill $(lsof -ti:8080,8081,8082,8083,7000,7001,7002,7003)

python3 apps/fabric/test/test_server.py 0 &> apps/fabric/log/server/log_0.txt &
python3 apps/fabric/test/test_server.py 1 &> apps/fabric/log/server/log_1.txt &
python3 apps/fabric/test/test_server.py 2 &> apps/fabric/log/server/log_2.txt &
python3 apps/fabric/test/test_server.py 3 &> apps/fabric/log/server/log_3.txt &

sleep 2

python3 apps/fabric/test/test_cmp.py
#python3 apps/fabric/test/test_mul.py