import boto3
import time

STACK_NAME = "polystudent-vpc-stack"
TEMPLATE_FILE = "vpc.yml"   

AWS_ACCESS_KEY_ID = 'ASIA4MTWNP4HWGVX2MEI'
AWS_SECRET_ACCESS_KEY = '3qSBYQkvQ8JQjA89GfFgSEUdAPIlHU1lFRL7rSWJ'
REGION_NAME = 'us-east-1' 
SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEAIaCXVzLXdlc3QtMiJIMEYCIQC9WOrI8cGQjPmcMbtz/rR2hMh7CLsWXId8OyQxQUgWyAIhAMjo2D9nnOvnzzIdKzsLh/v/rDKSQYjpV3H83qT/vgvlKscCCMv//////////wEQABoMODUxNzI1NjE0ODYzIgxbNHTK3/MQp+/kvWQqmwIaoMGlIRaFcrbLsnzwjqb47aRP6ZSmXlKYbFQMlD8w2oGWRbGBxF1jVXiblQ0/+Si1tiFniglXJEwFKAiyBErNO7I4b9da+xZ7YNM5j62LtXeqs60WQchvqDKnkivJ+wTuXLQiWbhAIlKKiD3wf5z+zJIwFI+XIrrlTy80V+KMA4DEpA0igKIgOXSVfoJ/T4WMKkYatdSeBNk2sXoJK873uf+IIGL10qZWXDpgjH+tWab3iqPHMTZzTycKHFXtELPeWeGRDs32GdRXWdBgmyvOGsPm/aM9x7r451pCCMz9tcossdONUByzaUjSSuBkRkJBfKipCMxUr7FLSzYcwP6eUy/xQ6asqpHh4uWr+dEiF6nkDa2g2sNBFcchMOWk48kGOpwBqFVdX3YIOtnwIk1t5R/n9wJUwUqDHqRk30ceUxPLIBl5cIFdXkpb+1ei+i4fCY1q+sLcwSNfQvrKMWHoPQH7/LeaQYBsL3em/ghQGo9V0UZ46EUnIt8dsgeJ1C5PbVmRwsJ46szjfEL7VpDzcYLV635QgEa7figX/VKZ7kBj3OQF36m4VrS37e3i7V08pHjxbrCNY+k7FLSMJGAB'

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
