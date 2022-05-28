import os

print("Stopping old containers")
os.system("powershell.exe docker stop $(docker ps --all --quiet)")
print("Removing old containers")
os.system("powershell.exe docker rm $(docker ps --all --quiet)")
print("Build new Containers")
os.system("powershell.exe docker-compose build")
print("Run new Containers")
os.system("powershell.exe docker-compose up")
