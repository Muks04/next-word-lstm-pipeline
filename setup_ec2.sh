#!/bin/bash
# Run this on your EC2 instance after SSH-ing in

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv -y

# Create app directory
mkdir -p ~/app && cd ~/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install tensorflow==2.21.0 numpy streamlit

echo "Setup complete. Upload your app files and run: streamlit run app1.py --server.port 8501"
