# Flask OWASP Project


## Requirements
- Python 3.x
- Flask

### To run it:
- pip install -r requirements.txt
- python run.py

### To run the Docker:
- docker compose build
- docker compose up

### To run the env (Kali):
- python3 -m venv venv   
- source venv/bin/activate  


### To run SonarQube (For Kali Linux):
- docker run -d --name sonarqube -p 9000:9000 sonarqube

after done this change the sonar.projectKey according to the project name
change sonar.login with coppied token

- npm install -g sonar-scanner  
- sonar-scanner

### To get bandit results
- pip install bandit
- bandit -r .



