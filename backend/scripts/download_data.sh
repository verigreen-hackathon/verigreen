#!/bin/bash
#
# Download Sentinel-2 data for VeriGreen
# This script downloads the required satellite imagery data that is not stored in git
#

echo "VeriGreen Data Download Script"
echo "=============================="
echo ""
echo "This will download Sentinel-2 satellite imagery for Sabangau National Park."
echo "Files will be saved to: data/raw/sentinel/"
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the backend directory"
    exit 1
fi

# Run the Python download script
echo "Starting download..."
python3 scripts/test_download.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Download completed successfully!"
    echo "Files downloaded to: ../data/raw/sentinel/"
    ls -la ../data/raw/sentinel/
else
    echo ""
    echo "Download failed. Please check the error messages above."
    exit 1
fi 