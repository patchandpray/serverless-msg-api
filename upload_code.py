#!env/bin/python3

import os
import io
import sys
import zipfile as zf
import yaml
import boto3
import json
import argparse

client = boto3.client('lambda')

def process_code(code_file):
    ''' Process lambda function from code file for posting to AWS. '''

    function_str = open(code_file, 'r')
    file_name = code_file.split('.')[0] + '.zip'

    zip_info = zf.ZipInfo(code_file)
    zip_info.external_attr = 0o744 << 16

    zip_file = zf.ZipFile(file_name, 'w', zf.ZIP_DEFLATED)
    zip_file.writestr(zip_info, function_str.read())
    zip_file.close()
    return file_name

def upload_lambda_function(zip_file, **kw):
    """ Function for creating a new lambda function. """

    with open(zip_file, 'rb') as f:
        zipped_code = f.read()

    response = client.create_function(
        FunctionName = kw['function_name'],
        Runtime = 'python3.6',
        Role = kw['iam_role'],
        Handler = kw['handler'],
        Code = {'ZipFile': zipped_code},
        Description = kw['description'],
        Timeout = kw['timeout'],
        MemorySize = kw['memory_size'],
        Publish = kw['publish'],
        Environment = kw['environment'],
        Tags = kw['tags']
    )
    print(json.dumps(response, indent=4))

def update_lambda_function(zip_file, **kw):
    """ Function for updating an existing lambda function code."""

    with open(zip_file, 'rb') as f:
        zipped_code = f.read()

    response = client.update_function_code(
        FunctionName = kw['function_name'],
        ZipFile = zipped_code,
        Publish = kw['publish'],
    )
    
    print(json.dumps(response, indent=4))

def update_lambda_configuration(**kw):
    """ Function for updating an existing lambda configuration."""

    response = client.update_function_configuration(
        FunctionName = kw['function_name'],
        Runtime = 'python3.6',
        Role = kw['iam_role'],
        Handler = kw['handler'],
        Description = kw['description'],
        Timeout = kw['timeout'],
        MemorySize = kw['memory_size'],
        Environment =  kw['environment'],
    )

    print(json.dumps(response, indent=4))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Helper tool for uploading code to AWS Lambda.")
    parser.add_argument('-n', dest='new_function', action='store_true',
                        help='Supply this argument to create a new function')
    parser.add_argument('-f', dest='code_file', action='store',
                        help='The lambda function code to be uploaded')
    parser.add_argument('-c', dest='config_file', action='store',
                        help='The configuration file for the lambda function')
    parser.add_argument('-u', dest='update', action='store_true',
                        help='Supply this argument to update an existing function')
    parser.add_argument('-z', dest='zip_file', action='store',
                        help='Zip file containing function code')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if not args.config_file:
        print('Please supply a configuration file for the lambda function.')
        sys.exit(1)
    with open(args.config_file, 'r') as config_file:
        cfg = yaml.load(config_file)
        print(cfg)

    if args.code_file:
        zip_file = process_code(args.code_file)
    elif args.zip_file:
        zip_file = args.zip_file
    if args.update:
        update_lambda_function(zip_file, **cfg)
        update_lambda_configuration(**cfg)
    if args.new_function:
        upload_lambda_function(zip_file, **cfg)
