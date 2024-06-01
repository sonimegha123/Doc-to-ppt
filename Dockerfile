# Use an official Python runtime as a parent image
FROM python:3.9

# Install pandoc
RUN apt-get update && apt-get install -y pandoc

ENV PANDOC_PATH /usr/bin/pandoc

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port available to the world outside this container
EXPOSE 8000

# Define command to run the app
CMD ["uvicorn", "api1:app", "--host", "0.0.0.0", "--port", "8000"]
