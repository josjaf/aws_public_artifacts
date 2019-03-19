# AWS Organizations IP Querying

Application (run.py) uses cross account roles to collect the IP range of all VPCs in an organization.  Users will need to ensure the proper cross account roles are created for each account.
Application process flow:
1. Assumes role in Org Master to list all accounts
2. Assumes Default Cross Account role to each child account to list regions and then describe VPCs in each region
3. Returns results and appends a CSV file with the following values:  AccountId,	CIDR Block,	VpcId,	Region located.

This application uses threading to speed up the process of querying the regions of each account.  Users will notice a momentary spike in local machine resources as the threads and sessions are created and the APIs invoked.
