#!/bin/bash

while true
do
    python3 scrap.py

    exit_code=$?

    # Check if the exit code matches the one you want
    if [ $exit_code -eq 1 ]; then
        echo "Python program exited with code 1, closing..."
        break
    else
        echo "Python program restarting....."
    fi
done
