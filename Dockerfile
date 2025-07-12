# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all project files
COPY . .

# Expose port (Render uses 10000 internally but exposes 0.0.0.0)
EXPOSE 10000

# Start the app using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
