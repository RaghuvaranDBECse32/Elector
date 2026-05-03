FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install flask google-generativeai firebase-admin
CMD ["python", "app.py"]
