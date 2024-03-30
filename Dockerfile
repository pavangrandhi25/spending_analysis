#base image
FROM python:3.10-alpine 

#Set the working directory in the container
WORKDIR /usr/spending_app

# Set the environment variable for the GitHub secret
ARG SERVICE_ACCOUNT_JSON
ENV SERVICE_ACCOUNT_JSON=$SERVICE_ACCOUNT_JSON

# Set the environment variable for the secret key
ARG SECRET_KEY
ENV SECRET_KEY=$SECRET_KEY

# Set the environment variable for the DB_NAME
ARG DB_NAME
ENV DB_NAME=$DB_NAME

# Create the JSON file from the environment variable
RUN mkdir -p /usr/spending_app/env_folder
RUN echo "$SERVICE_ACCOUNT_JSON" > /usr/spending_app/env_folder/service_account_api.json

# Install build dependencies
RUN apk add g++ make musl-dev linux-headers
RUN apk add gcc gfortran musl-dev libffi-dev openssl-dev

#Copy the requirements file into the container
COPY ./requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container
COPY ./ ./

# Change working directory to /src
WORKDIR /usr/spending_app/src/

# Startup command to run the application
CMD ["python3", "app.py"]
