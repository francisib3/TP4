import json
import uuid
import os

import boto3
from botocore.exceptions import ClientError


TEMPLATE_FILE = os.path.join(os.getcwd(), "s3.json")
STACK_NAME = "tp4-s3-bucket-stack"

AWS_ACCESS_KEY_ID = 'ASIA4MTWNP4HXFJRIVNO'
AWS_SECRET_ACCESS_KEY = 'naXW3ENsw1SneUssMIElQTXOC8j24r34jf4eio/l'
SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEA8aCXVzLXdlc3QtMiJGMEQCIB1gauhvPoQWypljUKaUvlAPcsysLH0kjf+u9bBeKwtqAiB4k5z4/9chkq1ILMnP59akFRjYbdbR/1Xtd4d6puKX2CrHAgjY//////////8BEAAaDDg1MTcyNTYxNDg2MyIMdZbatfIQJog0S2sEKpsCa/Q1qeQ5iSoVG89pECxnOhq5h/MTe8EhPSD9s9mfj1ya0y0oRv+eT9nuo3qsKwSgwLEIGMw9GK534Ld5REb1R5E2CYG2ALh97LqmmxjVI2nB37x6y+DV750ZyGzDzDyqlIeFMM/B9P4i5bRUb4p2AIVP+HlWjWhNL1T2P9D1XXtzAb6fT+XPcZyOZ3OOZK5TKg6lh3Pk9y9sjd0qmqx6jAKu3zMJxrByArV1l8KuDj8VHGXxcoE+dYODyA1Be4EvutUfT3AuuP9aaBBxwwhxgF4saezznjci+gN/brwDiIe/X3FCRIc7rr2vUk6/Npc5K/VGfTB0mva/l7asKT0ewcwn/hTtlqf9lSd5movt3FvFkvgh6GJNFZdgITCBlObJBjqeAenDpUON3L/NBRrh5feY1rDvMp16jVNP5cIeXMYcNxttBSYFif6wV1GaaKGkURk4kJ2cDpXiRD6gjfN9OMV1RtWKhpphzpWuOFxtWOaMRfcTi57diaxP+ddnsROYRUTzZT8eJrvz0sI0iPJ/3esbK3zyoiUTBZb78moSydOZhMNxfCUKL+IcDLUT29rPKXWSPz9pODIO9a/jqCJe9abl'
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
