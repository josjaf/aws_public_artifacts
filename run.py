import boto3


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
    return

if __name__ == '__main__':
    main()