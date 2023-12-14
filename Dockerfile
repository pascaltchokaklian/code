# Use the official Python image as the base image
FROM python:3.11.7

# Set the working directory in the container
WORKDIR /StravaWebsite-master

# Copy the application files into the working directory
COPY . /StravaWebsite-master

# Install new pip
RUN pip install --upgrade pip

RUN pip install --root-user-action=ignore

# Install the application dependencies
RUN pip install -r requirements.txt

# Define the entry point for the container
CMD ["python", "manage.py", "runserver", "0.0.0.1:8000"]