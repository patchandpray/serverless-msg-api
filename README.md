# SERVERLESS-MSG-API with AWS Lambda

Running a serverless MSG API using AWS Lambda

## What is it

A simple secure application for sending email messages and retrieving information
about earlier sent messages built on AWS lambda using DynamoDB as a backend.

Repository also contains tools for setting up the necessary environment and
uploading locally developed code to AWS Lambda.

This application uses the following AWS services:

* Lambda
* DynamoDB
* API Gateway
* AMI
* SES

The following tools are provided:

* setup\_environment.py
* upload\_code.py

### How it works

Upon posting a message to a email endpoint (msg\_id) the message is sent
using SES and stored in dynamodb in a table called 'messages'.
It is possible to store message content encrypted by supplying
store\_secure=True as a parameter to the API when using POST.
Messages for a certain msg\_id (email address) can be retrieved by issuing
a GET request to the /msg API endpoint.

This will return a list of all messages sent for this particular msg\_id.

### Design considerations

why use ses
possible different implentation for sending sms and encrypting messages

### Security considerations

* API Gateway GET and POST methods require authorization via and api authentication
token.
* Traffic to API gateway endpoints are encrypted via SSL.
* Lambda Environment variables are encrypted at rest using aws lambda builtin
encryption key.
* Dynamodb table is encrypted at rest by setting SSES to True.
* Optionally it is possible to additionally encrypt msg content stored in dynamodb
by passing the store\_secure=True parameter on POST. This will encrypt the msg
content before storing it in dynamodb. This might be usefull for handling sensitive
data in for example, complying with security standards or GDPR.

### DynamodDB messages Table model

* msg\_id [HASH key, string]
* timestamp [RANGE key, string]
* msg [string]
* subject [string]

### API Endpoint /msg

The /msg endpoint is the implementation for sending messages to an external
endpoint and retrieving them for inspection.

The API currently requires the following parameters:

**GET**: 
* msg\_id=email\_address (string)

**POST**:
* msg\_id=email\_address (string)
* msg=message\_content (string)
* subject=message\_subject (string)
* store\_secure=Boolean (True|False)

Please note that no restriction is currently placed on input parameters.

## How to set it up

### Requirements

* An AWS account with AWS keypair and admin privileges (for creating the environment)
* aws cli
* make

If building locally:
* Python 3.6
* Python3 module venv (for creating the virtualenvironments)
* pip

If building using docker:
* docker

**Please note that `setup_environment.py` is currently NOT idempotent, it is a
one off atomic operation for setting up the environment.**

### Using Docker

from your local machine set up aws cli:
`aws configure`

add your aws-region, aws-account-id and email address to use for ses to
`env_config.yml`

update the lambda configuration file `main.yml`:
substitute `aws_account_id` for your aws-account-id and `sender_email` for the
email address to be used with ses

run `make docker-build`
run `make docker-run` 

run `python3 -m venv lambdaenv`
run `source lambdaenv/bin/activate`
run `pip install -r lambda_requirements.txt`
exit the lambdaenv `deactivate`

run `make zip`

setup the environment for running serverless-msg-api:
run `make setup-env`

### Using local environment

from repository root:

Configure aws with your region and account that has privileges to setup the
environment:
`aws configure`

add your aws-region, aws-account-id and email address to use for ses to
`env_config.yml`

update the lambda configuration file `main.yml`:
substitute `aws_account_id` for your aws-account-id and `sender_email` for the
email address to be used with ses

install dependencies for the lambda function:
run `python3 -m venv lambdaenv`
run `source lambdaenv/bin/activate`
run `pip install -r lambda_requirements.txt`
exit the lambdaenv `deactivate`

install dependencies for creating the environment:
run `python3 -m venv env`
run `source env/bin/activate`
run `pip install -r requirements.txt`

from the env virtualenvironment:
create the zip file containing the lambda function code and dependencies:
run `make zip`

setup the environment for running serverless-msg-api:
run `make setup-env`

## Use the msg API using POST and GET

!! Be sure to validate your email address that you specified in env\_config.yml.
Go to your Email.
Verify your Email address so that it can be uses with SES.

use `make post` for posting a message using the msg api
use `make get` for getting all messages for your email address

## Notes

### setup\_environment.py

setup\_environment.py does the following:

* Generates the lambda IAM policy document from jinja template
* Sets up IAM policy role and attached trust and policy document
* Creates the dynamodb table `messages` with encryption at rest
* Uploads the lambda function with configuration
* Creates the api gateway with resource, methods, authorization key and deployment
* Adds sender email to ses so lambda can send email messages

### upload\_code.py

Development tool implementing methods for:

Zipping lambda function code
Uploading lambda function code
Updating lambda function code
Updating lambda function configuration

### Destroying the environment

Since currently no option is provided for automatically bringing down the
environment do the following:

Log in to the AWS Console
Remove your email address from SES
Delete the dynamodb table `messages`
Remove the IAM role `msg_api_role`
Delete the lambda function `msg_api`
Delete the API gateway `msg-api`

### What could be improved

* Making setup\_environment idempotent when creating the environment.
* Provide a destroy environment option for setup\_environment.py.
* Use Terraform for setting up the environment as it is idempotent by default.
* Use API Gateway client certificates for verifying data coming from the backend.
* Seperate Lambda functions for encrypting using sqs service when store\_secure is
provided.
* Provide POST parameters like msg content and subject in POST body.
* Seperate endpoint for decrypting encrypted messages (ccurently no option is
provided for decrypting store\_secure message content).
* Logging for api gateway.
* Strict allowing of api parameters on API Gateway (currently all parameters are
* forwarded since we use AWS\_PROXY) and parameters are not error handled at
* lambda side.
* Better error handling in lambda function.
* Automatically add API documentation in API Gateway.
* Testset for testing developed lambda code.
