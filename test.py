import uuid
import os
import threading
import csv

import boto3
import botocore


def get_child_session(account_id, role_name, session=None):
    """
    get session, with error handling, allows for passing in an sts client. This allows Account A > B > C where A cannot assume a role directly to C
    :param account_id:
    :param role_name:
    :param sts:
    :return:
    """
    # “/“ + name if not name.startswith(“/“) else name
    try:
        # allow for a to b to c if given sts client.
        if session == None:
            session = boto3.session.Session()


        client = session.client('sts')


        response = client.get_caller_identity()
        # remove the first slash
        role_name = role_name[1:] if role_name.startswith("/") else role_name
        # never have a slash in front of the role name
        role_arn = 'arn:aws:iam::' + account_id + ':role/' + role_name
        print("Creating new session with role: {} from {}".format(role_arn, response['Arn']))

        response = client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=str(uuid.uuid1())
        )
        credentials = response['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        return session
    except botocore.exceptions.ClientError as e:

        if e.response['Error']['Code'] == 'AccessDenied':
            print(e)
            #raise Exception(e)

        elif 'Not authorized to perform sts:AssumeRole' in str(e):
            print(e)
            #raise Exception(f"ERROR:Not authorized to perform sts:AssumeRole on {role_arn}")
        else:
            print(e)
            #raise Exception(e)

    finally:
        pass

def get_org_accounts(session):
    org_client = session.client('organizations')
    account_ids = []
    response = org_client.list_accounts()
    for account in response['Accounts']:
        account_ids.append(account['Id'])
    while 'NextToken' in response:
        response = org_client.list_accounts(NextToken=response['NextToken'])
        for account in response['Accounts']:
            account_ids.append(account['Id'])
    return account_ids


def main():
    session = boto3.session.Session()
    org_accounts = get_org_accounts(session)
    role_name = os.environ.get('RoleName', 'OrganizationAccountAccessRole')

    for account in org_accounts:
        child_session = get_child_session(account_id=account, role_name=role_name, session=None)
        ec2 = child_session.client('ec2')
        # response = ec2.create_vpc(
        #     CidrBlock='10.10.10.0/24',
        #     AmazonProvidedIpv6CidrBlock=False,
        #     InstanceTenancy='default')
        #print(response)
        response = ec2.describe_vpcs()
        print(response)
        vpc = [v for v in response['Vpcs'] if v['CidrBlock'] == '10.10.10.0/24'][0]['VpcId']
        response = ec2.delete_vpc(VpcId=vpc)
        print(response)
    return
if __name__ == '__main__':
    main()