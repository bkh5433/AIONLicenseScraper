FROM python:3.12.3-alpine3.20


# Set the working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

RUN chmod +x version.sh && sh ./version.sh

# env variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0


# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

