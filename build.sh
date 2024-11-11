#!/bin/bash
pip install -r requirements.txt

nuitka --standalone --onefile --output-filename=catflipper CF-Handler.py
