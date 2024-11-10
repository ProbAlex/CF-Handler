#!/bin/bash
pip install -r requirements.txt

echo "Compiling for Linux..."
nuitka --standalone --onefile --output-filename=catflipper CF-Handler.py
