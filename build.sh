#!/bin/bash

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Compiling for Linux..."
    nuitka --standalone --onefile CF-Handler.py

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "Compiling for Windows..."
    nuitka --standalone --onefile --windows-disable-console CF-Handler.py
else
    echo "Unsupported OS"
fi
