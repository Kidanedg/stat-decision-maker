# Use official Python 3.10 image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all project files to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Render uses
EXPOSE 10000

# Start the Flask app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
