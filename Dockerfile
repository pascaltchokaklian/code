# Use the official Python image as the base image
FROM python:3.11.7

# set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRTBYTECODE 1

# Set the working directory in the container
RUN mkdir /myapp

WORKDIR /myapp

# Copy the application files into the working directory
COPY . /myapp

RUN python -m venv /myapp/env

ENV PATH="/env/bin/:$PATH"

#################
# ADD Shell File
#################

COPY entrypoint.sh /myapp/entrypoint.sh
RUN python -m pip install --upgrade pip

# Install the application dependencies
COPY requirements.txt /myapp/

RUN pip install -r requirements.txt

EXPOSE 8000

# Copy the rest of the project files
COPY . .

# Define the entry point for the container
CMD ["python", "manage.py", "runserver", "127.0.0.1:8080"]
