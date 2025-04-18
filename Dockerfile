# Use an official Python runtime
FROM python:3.10-slim

# Set the working directory
WORKDIR .

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the Flask app
CMD ["python", "main.py"]
