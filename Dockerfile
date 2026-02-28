# Use official Python 3.10 slim image - avoiding python 3.14 to prevent pandas build issues
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for NLTK, scipy, and pandas
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (defaulting to 10000 to match typical cloud platforms like Render, or 5000 for local)
ENV PORT=5000
EXPOSE $PORT

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
