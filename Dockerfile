# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (for Docker caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . .

# Set entrypoint to run the script
CMD ["python", "main.py"]
