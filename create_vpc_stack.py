import boto3
import time

STACK_NAME = "polystudent-vpc-stack-3--2"
TEMPLATE_FILE = "vpc.yml"   

AWS_ACCESS_KEY_ID = 'ASIA4MTWNP4H5JP2LGJD'
AWS_SECRET_ACCESS_KEY = 'ii7b4ll2PDdkCUKbf7ZTb19NOEQ3Yd/jLLu7nmXf'
SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEBoaCXVzLXdlc3QtMiJHMEUCIQCQWAwne+RYlZ3JgC6HRBKJiRPUXBzyAp5Sw+YuZqOg8AIgaAEkr0OWe/XqVO5grk3uKtqik70ZWf5UA/Ru4xfMU70qxwII4///////////ARAAGgw4NTE3MjU2MTQ4NjMiDLnfbZKzP0S6MJ9QsCqbArRNxHFRDnmXo2RH+PS6ZLHprUy+5dgrs/8u5zeNqVCK15B7v2af61uCyBQPCNKF8XzHri2XfTCJeitYdvxGBsg/bapReSMJD/X9UksdwoNY1+8ui/ZTfB9gwINGgOAsxkMhRgjIwfTlhxv51aTsMducnh5ZPSx9z0tmUjX/zoImJRPgIg3uLSpjKyNsFag6kGNf6w5Os6EAZTmeK085sO1/Wh8A6Pfr2uXbV7SNB8o5uc4iSp3t573djeTk0xN47nj4QJfdjrrJq+/WJbfaXWzT2+W8qTaWPxgkTSPqMsY3KL8qpi/1+4T4XqcmlZrwRNOw4PiAMhhW86biVqVnD3f+RoUleBFVS7pUDxfL5P/ywcE5VWvw4Z7OZ8Iwxr7oyQY6nQFES6yVgswn9qLccQ90jVAzJNp2X9RtvE/txxFD3SN1I7gdERQiaRFvt8p5h5yXE4jEeKTc0i/v+/TNRqmtDvlHLR6Yi1fVk0nTRPWyZB/65bl97aXnFLf2CpLngD5p/dBab0kxwOP0bTNQMmVuvqmSD1sN0H8HyFnzScI4zTrAOO4HgUn/CLSUFojfOIbDi5VC8Nn80tv0/ChWFS5/'
REGION_NAME = 'us-east-1' 
S3_BUCKET_NAME = "polystudents3-tp4-1962292-c10da905"

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
        {"ParameterKey": "FlowLogsBucketName", "ParameterValue": S3_BUCKET_NAME}
    ]

    print(f"Creating stack {STACK_NAME} ...")
    try:
        response = cf.create_stack(
            StackName=STACK_NAME,
            TemplateBody=template_body,
            Parameters=parameters,
            OnFailure="ROLLBACK",
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )
        waiter = cf.get_waiter("stack_create_complete")
        waiter.wait(StackName=STACK_NAME)
        print(f"Stack {STACK_NAME} created successfully.")
    except:
        response = cf.update_stack(
            StackName=STACK_NAME,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )
        waiter = cf.get_waiter("stack_update_complete")
        waiter.wait(StackName=STACK_NAME)
        print(f"Stack {STACK_NAME} updated successfully.")



    stack = cf.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
    print("\nOutputs:")
    for output in stack.get("Outputs", []):
        print(f"  {output['OutputKey']}: {output['OutputValue']}")

if __name__ == "__main__":
    main()
