import uuid
import boto3

def get_child_session(account_id, role_name, sts=None):
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
        if sts == None:
            client = boto3.client('sts')
        else:
            client = sts


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
            raise Exception(e)

        elif 'Not authorized to perform sts:AssumeRole' in str(e):
            raise Exception(f"ERROR:Not authorized to perform sts:AssumeRole on {role_arn}")
        else:
            raise Exception(e)

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
    print(org_accounts)
    for account in org_accounts:
        print(f"Processing Account: {account}")
        child_session = get_child_session(account_id=account, role_name='OrganizationAccountAccessRole', sts=None)
        ec2 = child_session.client('ec2')
        #response = ec2.describe_vpcs()
        #print(response)

        region_list = [region['RegionName'] for region in ec2.describe_regions()['Regions']]

        for region in region_list:
            child_account = session.client('ec2', region_name=region)
            vpcs = child_account.describe_vpcs()
            for vpc in vpcs['Vpcs']:

                if vpc['IsDefault'] == True:
                    print('Default VPC  //       ' + 'VPC ID: ' + vpc['VpcId'] + '//' + 'IP Range: ' + vpc['CidrBlock'])
                else:
                    print('User Created VPC  //  ' + 'VPC ID: ' + vpc['VpcId'] + '//' + 'IP Range: ' + vpc['CidrBlock'])
    return

if __name__ == '__main__':
    main()