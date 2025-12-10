import boto3
import time

STACK_NAME = "polystudent-vpc-stack"
TEMPLATE_FILE = "vpc.yml"   

REGION_NAME = 'us-east-1' 

def main():

    cf = boto3.client(
        "cloudformation",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=SESSION_TOKEN,
        region_name=REGION_NAME
        )


    with open(TEMPLATE_FILE, "r") as f:
        template_body = f.read()

    parameters = [
        {"ParameterKey": "EnvironmentName",    "ParameterValue": "polystudent-vpc-boto"},
        {"ParameterKey": "VpcCIDR",            "ParameterValue": "10.0.0.0/16"},
        {"ParameterKey": "PublicSubnet1CIDR",  "ParameterValue": "10.0.0.0/24"},
        {"ParameterKey": "PublicSubnet2CIDR",  "ParameterValue": "10.0.16.0/24"},
        {"ParameterKey": "PrivateSubnet1CIDR", "ParameterValue": "10.0.128.0/24"},
        {"ParameterKey": "PrivateSubnet2CIDR", "ParameterValue": "10.0.144.0/24"},
    ]

    print(f"Creating stack {STACK_NAME} ...")
    response = cf.create_stack(
        StackName=STACK_NAME,
        TemplateBody=template_body,
        Parameters=parameters,
        OnFailure="ROLLBACK" 
    )

    waiter = cf.get_waiter("stack_create_complete")
    waiter.wait(StackName=STACK_NAME)
    print(f"Stack {STACK_NAME} created successfully.")

    stack = cf.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    print("\nOutputs:")
    for output in stack.get("Outputs", []):
        print(f"  {output['OutputKey']}: {output['OutputValue']}")

if __name__ == "__main__":
    main()
