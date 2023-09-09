FROM python:3.10.12

# Create the working directory
RUN set -ex && mkdir /translator
WORKDIR /translator

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy the relevant directories
COPY . ./

# Run the web server
ENV PYTHONPATH /translator
CMD python3 /translator/app.py