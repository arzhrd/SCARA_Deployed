# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file for the frontend
COPY requirements_frontend.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements_frontend.txt

# Copy the Streamlit app code into the container
COPY streamlit_frontend.py .

# Make port 8080 available to the world outside this container
# Streamlit Cloud expects the app to be on this port
EXPOSE 8080

# Define environment variable to tell Streamlit where to run
ENV PORT=8080
ENV HOST=0.0.0.0

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_frontend.py"]
