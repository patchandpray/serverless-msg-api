#!/usr/bin/env sh
# script for cleaning up files and directories created by setting up environment
rm -v api_id api_key aws_region ses_email msg_api_policy.json
rm -v -rf main.zip
rm -v -rf env
rm -v -rf lambdaenv
