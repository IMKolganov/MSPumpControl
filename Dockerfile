# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install curl and download wait-for-it.sh
RUN apt-get update && apt-get install -y curl \
    && curl -o /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

# Copy dependencies and install them
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy all files to the working directory
COPY . .

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=docker

# Expose port 5004 for Flask
EXPOSE 5004

# Define the command to run the application
CMD ["wait-for-it.sh", "rabbitmq:5672", "--", "python", "run.py"]
