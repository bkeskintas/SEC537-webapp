# Flask OWASP Project


## Requirements
- Python 3.x
- Flask

To run it:

python run.py

To run the Docker:
- docker build -t flask_app .
- docker run -p 5000:5000 flask_app

To run the env (Kali):
python3 -m venv venv   
source venv/bin/activate  


To run SonarQube (Kali):
>docker run -d --name sonarqube -p 9000:9000 sonarqube

after done this change the sonar.projectKey according to the project name
change sonar.login with coppied token

>npm install -g sonar-scanner  
>sonar-scanner


