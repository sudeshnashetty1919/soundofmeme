# Base image
FROM python:3.9

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install webdriver-manager

# Set working directory
WORKDIR /app

# Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    libnss3 \
    libgconf-2-4 \
    libx11-xcb1 \
    fonts-liberation \
    libasound2 \
    libatk1.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcurl4 \
    libxshmfence-dev \
    libunwind8 && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb && \
    google-chrome --version  # Verify Chrome installation

# Create directory for storing chromedriver and ensure permissions
RUN mkdir -p /usr/local/bin/chromedriver && \
    chmod -R 755 /usr/local/bin/chromedriver

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Set ChromeDriver in PATH
ENV PATH="/usr/local/bin/chromedriver:$PATH"

# Copy project files to the container
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the Python script
CMD ["python", "mainwithcookies.py"]
