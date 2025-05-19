#!/bin/bash

# Создаем корневую директорию проекта
mkdir -p project/{service1,service2,k8s}
cd project || exit

# Создаем структуру service1
mkdir -p service1/templates
cat > service1/Dockerfile <<EOL
# service1/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
EOL

cat > service1/requirements.txt <<EOL
Flask==2.3.3
Flask-SQLAlchemy==3.1.1
EOL

cat > service1/app.py <<EOL
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Service 1"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOL

cat > service1/templates/index.html <<EOL
<!DOCTYPE html>
<html>
<head><title>Service 1</title></head>
<body>
<h1>Welcome to Service 1</h1>
</body>
</html>
EOL

# Создаем структуру service2
mkdir -p service2/templates
cat > service2/Dockerfile <<EOL
# service2/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
EOL

cat > service2/requirements.txt <<EOL
Flask==2.3.3
EOL

cat > service2/app.py <<EOL
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Service 2"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOL

cat > service2/templates/index.html <<EOL
<!DOCTYPE html>
<html>
<head><title>Service 2</title></head>
<body>
<h1>Welcome to Service 2</h1>
</body>
</html>
EOL

# Создаем docker-compose.yml
cat > docker-compose.yml <<EOL
version: '3.8'

services:
  service1:
    build: ./service1
    container_name: service1
    ports:
      - "5001:5000"
    networks:
      - app-network

  service2:
    build: ./service2
    container_name: service2
    ports:
      - "5002:5000"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOL

# Создаем Kubernetes манифесты
cd k8s || exit

# service1-deployment.yaml
cat > service1-deployment.yaml <<EOL
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service1
  template:
    metadata:
      labels:
        app: service1
    spec:
      containers:
      - name: service1
        image: service1:latest
        ports:
        - containerPort: 5000
EOL

# service1-service.yaml
cat > service1-service.yaml <<EOL
apiVersion: v1
kind: Service
metadata:
  name: service1
spec:
  selector:
    app: service1
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
EOL

# service2-deployment.yaml
cat > service2-deployment.yaml <<EOL
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service2
  template:
    metadata:
      labels:
        app: service2
    spec:
      containers:
      - name: service2
        image: service2:latest
        ports:
        - containerPort: 5000
EOL

# service2-service.yaml
cat > service2-service.yaml <<EOL
apiVersion: v1
kind: Service
metadata:
  name: service2
spec:
  selector:
    app: service2
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
EOL

# argocd-application.yaml
cat > argocd-application.yaml <<EOL
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-microservices
spec:
  destination:
    namespace: default
    server: https://kubernetes.default.svc 
  sources:
  - repoURL: https://github.com/yourusername/yourrepo.git 
    targetRevision: HEAD
    path: service1
  - repoURL: https://github.com/yourusername/yourrepo.git 
    targetRevision: HEAD
    path: service2
  project: default
EOL

cd ..

echo "✅ Структура проекта создана успешно!"
echo "📁 Дерево структуры:"
find . -type f | sed 's|^\./||' | sort | awk '
{
    split($0, a, "/");
    for (i=1; i<=length(a); i++) {
        printf "%*s%s\n", (i-1)*4, "", a[i];
    }
}' | sed 's/ /-/g; s/-\([^-]\)/ ─\1/'
