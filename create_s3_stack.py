import json
import uuid
import os

import boto3
from botocore.exceptions import ClientError


TEMPLATE_FILE = os.path.join(os.getcwd(), "tp4-s3.json")
STACK_NAME = "tp4-s3-bucket-stack"

REGION_NAME = 'us-east-1' 

def load_and_adjust_template(template_path: str) -> str:
    with open(template_path, "r") as f:
        template_dict = json.load(f)

    bucket_props = (
        template_dict["Resources"]["S3Bucket"]["Properties"]
    )

    base_name = bucket_props.get("BucketName", "polystudents3-tp4-1962292")
    suffix = str(uuid.uuid4())[:8]
    new_bucket_name = f"{base_name}-{suffix}"

    bucket_props["BucketName"] = new_bucket_name

    print("Using bucket name:", new_bucket_name)

    return json.dumps(template_dict)


def main():
    template_body = load_and_adjust_template(TEMPLATE_FILE)

    print("\n=== Final JSON template sent to CloudFormation (proof of IaC) ===")
    print(json.dumps(json.loads(template_body), indent=2))

    cf = boto3.client(
        "cloudformation",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=SESSION_TOKEN,
        region_name=REGION_NAME
        )
    try:
        print(f"\nCreating CloudFormation stack '{STACK_NAME}' in {REGION_NAME}...")
        cf.create_stack(
            StackName=STACK_NAME,
            TemplateBody=template_body,
            OnFailure="ROLLBACK",
        )

        waiter = cf.get_waiter("stack_create_complete")
        waiter.wait(StackName=STACK_NAME)
        print(f"\nStack '{STACK_NAME}' created successfully.")

        stack = cf.describe_stacks(StackName=STACK_NAME)["Stacks"][0]
        print("\n=== Stack Outputs (proof) ===")
        for output in stack.get("Outputs", []):
            print(f"{output['OutputKey']}: {output['OutputValue']}")

    except ClientError as e:
        print("\nCloudFormation error while creating the stack:")
        print("  Code   :", e.response["Error"]["Code"])
        print("  Message:", e.response["Error"]["Message"])


if __name__ == "__main__":
    main()
