# Small official Python image
FROM python:3.12-slim

# Print logs immediately, don't write .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (cached between builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application code
COPY app ./app

# Start the Slack bot (Socket Mode, no public URL needed)
CMD ["python", "-m", "app.slack.server"]