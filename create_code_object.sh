#!/usr/bin/env sh
python3 upload_code.py -f main.py -c main.yml
cd lambdaenv/lib/python3.6/site-packages
zip -r9 ../../../../main.zip .
