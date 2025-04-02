# Use a Python base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the local directory to the containerdocker build -t trustwallet-etl .
COPY . .

# Install the necessary dependencies (use a requirements.txt if available)
RUN pip install -r requirements.txt
# Or if you don't have a requirements.txt:
# RUN pip install requests

# Expose the port that the app will run ondocker run -d -p 5000:5000 trustwallet-etl
EXPOSE 5000

# Set the command to run the main script
CMD ["python", "main.py"]
