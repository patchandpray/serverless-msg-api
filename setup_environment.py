#!env/bin/python3

import sys
import boto3
import uuid
import json
from jinja2 import Template
import time
import yaml
import argparse

def generate_policy_document(**env_config):
    """ Generates a policy document from jinja2 template """

    with open('templates/msg_api_policy.json.j2') as j2_file:
        template = Template(j2_file.read())
    with open('msg_api_policy.json', 'w') as outfile:
        outfile.write(template.render(aws_region=env_config['aws_region'],
                                      aws_account_id=env_config['aws_account_id']))
    print('Templated policy document using aws-region: {aws_region} and aws-account-id: {aws_account_id}'.format(**env_config))

def setup_iam():
    """ Sets up the IAM trust and policy document that the lambda function requires """

    client = boto3.client('iam')
    trust_policy = json.loads(open('msg_api_trust_policy.json', 'rb').read())
    policy = json.loads(open('msg_api_policy.json', 'rb').read())

    setup_lambda_role = client.create_role(
        RoleName='msg_api_role',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role used by lambda msg_api function to take action upon AWs backend services',
        )
    print('Created lambda IAM role with id: {RoleId} and arn: {Arn}.'.format(**setup_lambda_role['Role']))
    attach_lambda_policy = client.put_role_policy(
        RoleName='msg_api_role',
        PolicyName='msg_api_policy',
        PolicyDocument=json.dumps(policy)
        )
    print('Attached IAM policy to {Arn}.'.format(**setup_lambda_role['Role']))

def setup_lambda_function(zip_file, **lambda_config):
    """ Sets up the lambda function with configuration """

    client = boto3.client('lambda')

    with open(zip_file, 'rb') as f:
        zipped_code = f.read()

    create_lambda = client.create_function(
        FunctionName = lambda_config['function_name'],
        Runtime = 'python3.6',
        Role = lambda_config['iam_role'],
        Handler = lambda_config['handler'],
        Code = {'ZipFile': zipped_code},
        Description = lambda_config['description'],
        Timeout = lambda_config['timeout'],
        MemorySize = lambda_config['memory_size'],
        Publish = lambda_config['publish'],
        Environment = lambda_config['environment'],
        Tags = lambda_config['tags']
    )
    print('Created lambda function: {FunctionName}'.format(**create_lambda))

def setup_dynamodb_table():
    """ Sets up the dynamodb table messages """

    client = boto3.client('dynamodb')
    create_table = client.create_table(
        TableName='messages',
        KeySchema=[
            {
                'AttributeName': 'msg_id',
                'KeyType': 'HASH',
            },
            {
                'AttributeName': 'timestamp',
                'KeyType': 'RANGE'
            }],
        AttributeDefinitions= [
            {
                'AttributeName': 'msg_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'timestamp',
                'AttributeType': 'S'
            }],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
            },
        SSESpecification={
            'Enabled': True
            }
        )
    print('Created DynamoDB table: {TableName} with Arn: {TableArn}.'.format(**create_table['TableDescription']))

def setup_ses(**env_config):
    """ Sets up the email address the lambda function will use for sending msg's """

    client = boto3.client('ses')
    email_address = env_config['email_address'],
    create_email = client.verify_email_identity(
        EmailAddress=email_address[0]
        )
    with open('ses_email', 'w+') as ses_email_file:
        ses_email_file.write(env_config['email_address'])

    print('Setup ses with email address: {}.\nPlease verify your email address so it can be used with ses.'.format(email_address[0]))

def setup_api_gateway(**env_config):
    """ Sets up the API gateway will authorization, methods, resources and execution permissions """

    name = 'msg-api'
    description = 'Serverless msg api'

    client = boto3.client('apigateway')
    lambda_client = boto3.client('lambda')
    
    api_key = client.create_api_key(
        name='msg-api-key',
        description=description + ' key',
        enabled=True
        )
    print('Created api key with id: {id} and value: {value}'.format(**api_key))

    with open('api_key', 'w+') as api_key_file:
        api_key_file.write(api_key['value'])

    rest_api = client.create_rest_api(
        name=name,
        description=description
        )
    print('Created rest api {} with id: {}'.format(rest_api['name'], rest_api['id']))

    with open('api_id', 'w+') as api_id_file:
        api_id_file.write(rest_api['id'])

    base_path = client.get_resources(
        restApiId=rest_api['id'],
        )
    resource = client.create_resource(
        restApiId=rest_api['id'],
        parentId=base_path['items'][0]['id'],
        pathPart='msg'
        )
    print('Created resource {} with id {}'.format(resource['path'],resource['id']))

    lambda_version = lambda_client.meta.service_model.api_version

    uri_data = {
        'aws_region': env_config['aws_region'],
        'api_version': lambda_version,
        'aws_account_id': env_config['aws_account_id'],
        'lambda_function_name': 'msg_api',
        'aws_api_id': rest_api['id']
        }

    uri = "arn:aws:apigateway:{aws_region}:lambda:path/{api_version}/functions/arn:aws:lambda:{aws_region}:{aws_account_id}:function:{lambda_function_name}/invocations".format(**uri_data)

    methods = {'GET': '200', 'POST': '201'}

    for method, value in methods.items():
        client.put_method(
            restApiId=rest_api['id'],
            resourceId=resource['id'],
            httpMethod=method,
            authorizationType='NONE',
            apiKeyRequired=True
            )
        client.put_integration(
            restApiId=rest_api['id'],
            resourceId=resource['id'],
            httpMethod=method,
            integrationHttpMethod='POST',
            uri=uri,
            type='AWS_PROXY',
            )
        client.put_integration_response(
            restApiId=rest_api['id'],
            resourceId=resource['id'],
            httpMethod=method,
            statusCode=value,
            selectionPattern=".*"
            )
        client.put_method_response(
            restApiId=rest_api['id'],
            resourceId=resource['id'],
            httpMethod=method,
            statusCode=value,
            )

        uri_data['method'] = method
        source_arn = "arn:aws:execute-api:{aws_region}:{aws_account_id}:{aws_api_id}/*/{method}/msg".format(**uri_data)

        lambda_client.add_permission(
            FunctionName=uri_data['lambda_function_name'],
            StatementId=uuid.uuid4().hex,
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
            )
    deployment = client.create_deployment(
        restApiId=rest_api['id'],
        stageName='dev',
        stageDescription='Development stage for serverless msg api'
        )
    print('Created deployment for rest api')

    usage_plan = client.create_usage_plan(
        name='msg_api_usage_plan',
        description='msg api usage plan',
        apiStages=[
            {
                'apiId': rest_api['id'],
                'stage': 'dev'
                }
            ]
        )
    print('Created usage_plan: {name} with apistages: {apiStages}'.format(**usage_plan))
    usage_plan_key = client.create_usage_plan_key(
        usagePlanId=usage_plan['id'],
        keyId=api_key['id'],
        keyType='API_KEY'
        )
    print('Attached api key to usage plan')

    deployment_uri = 'https://{aws_api_id}.execute-api.{aws_region}.amazonaws.com/dev/msg'.format(**uri_data)

    print('Succesfully created API Gateway for {}'.format(name))
    print('Deployment uri: {}'.format(deployment_uri))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tool to setup environment for serverless-msg-api")
    parser.add_argument('-e', dest='env_config', action='store',
                        help="Environment configuration file")
    parser.add_argument('-z', dest='zip_file', action='store',
                        help="The Zip file containing the lambda function code and dependencies")
    parser.add_argument('-c', dest='lambda_config', action='store',
                        help="The configuration file for the lambda function")
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if not (args.env_config):
        print('!! Please supply the environment configuration file.')
        parser.print_help()
        sys.exit(1)

    if not args.lambda_config:
        print('!! Please supply the lambda function configuration file.')
        parser.print_help()
        sys.exit(1)

    if not args.zip_file:
        print('!! Please supply the lambda function zip file.')
        parser.print_help()
        sys.exit(1)

    with open(args.env_config, 'r') as env_config_file:
        env_config = yaml.load(env_config_file)

    with open(args.lambda_config, 'r') as lambda_config_file:
        lambda_config = yaml.load(lambda_config_file)

    with open('aws_region','w+') as aws_region_file:
        aws_region_file.write(env_config['aws_region'])

    # Setup the environment
    generate_policy_document(**env_config)
    setup_iam()
    setup_dynamodb_table()
    time.sleep(10)
    setup_lambda_function(args.zip_file, **lambda_config)
    setup_api_gateway(**env_config)
    setup_ses(**env_config)

    print('Environment created succesfully.')
    print('\n!! Be sure to validate the email address you specified for using with SES !!')

