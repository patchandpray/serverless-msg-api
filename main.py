import os
import json
import datetime
import hashlib
import boto3
from boto3.dynamodb.conditions import Key
from simplecrypt import encrypt, decrypt
from base64 import b64encode, b64decode

def msg(event, context):
    """ Lambda handler for handling GET and POST Httpmethods for /msg API gateway endpoint. """
    session = boto3.Session(region_name='eu-west-1')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('messages')
    dynamo_client = session.client('dynamodb')
    ses_client = session.client('ses')

    msg_id = event['queryStringParameters']['msg_id']

    encryption_key = (os.environ['encryption_key'] + msg_id).encode().hex()
    sender_email = (os.environ['sender_email'])

    if event['httpMethod'] == 'GET':
        query_msg = table.query(
            KeyConditionExpression=Key('msg_id').eq(msg_id)
            )
        print(query_msg)
        
        return {
            "statusCode": 200,
            "body": json.dumps(query_msg)
        }

    if event['httpMethod'] == 'POST':
        msg = event['queryStringParameters']['msg']
        subject = event['queryStringParameters']['subject']

        send_email = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [
                    msg_id,
                    ]
                },
            Message={
                'Subject': {
                    'Data': subject,
                    },
                'Body': {
                    'Text': {
                        'Data': msg,
                        }
                    }
                }
            )

        timestamp = str(datetime.datetime.now())
        if event['queryStringParameters']['store_secure'] == 'True':
            msg = encrypt_msg(msg, encryption_key, msg_id)
        store_msg = dynamo_client.put_item(
            TableName='messages',
            Item={
                'msg_id': {'S': msg_id },
                'timestamp': {'S': timestamp },
                'msg': {'S': msg },
                'subject': {'S': subject }
                }
            )
        payload = "Msg sent and stored succesfully for {}".format(msg_id)

        return {
            "statusCode": 201,
            "body": json.dumps(payload)
        }

    else:
        return {
            "statusCode": 200,
            "body": json.dumps('Method not supported')
        }

def encrypt_msg(msg, encryption_key, msg_id):
    cipher = encrypt(encryption_key, msg)
    c_msg = b64encode(cipher)
    return c_msg.decode("utf-8")

# Currently not implemented
def decrypt_msg(c_msg, encryption_key, msg_id):
    cipher = b64decode(c_msg)
    msg = decrypt(encryption_key, cipher)
    return msg.decode("utf-8")
