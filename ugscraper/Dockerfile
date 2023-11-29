# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /usr/src/app

# Install ping and Redis CLI
RUN apt-get update && apt-get install -y \
    iputils-ping \
    redis-tools

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Run scrapy when the container launches
RUN pip install --no-cache-dir -r requirements.txt

CMD scrapy crawl ugscraper; tail -f /dev/nullexit
