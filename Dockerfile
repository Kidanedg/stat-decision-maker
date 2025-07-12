# Base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads folder (if used for session/file uploads)
RUN mkdir -p uploads

# Expose port (optional for docs, not needed by Render)
EXPOSE 8000

# Start with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
