FROM python:3.9-slim
WORKDIR /app
COPY service2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY service2/ .
EXPOSE 5000
CMD ["python", "app.py"]