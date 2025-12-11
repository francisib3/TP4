import json
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"


AWS_ACCESS_KEY_ID = 'ASIA4MTWNP4H5JP2LGJD'
AWS_SECRET_ACCESS_KEY = 'ii7b4ll2PDdkCUKbf7ZTb19NOEQ3Yd/jLLu7nmXf'
SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEBoaCXVzLXdlc3QtMiJHMEUCIQCQWAwne+RYlZ3JgC6HRBKJiRPUXBzyAp5Sw+YuZqOg8AIgaAEkr0OWe/XqVO5grk3uKtqik70ZWf5UA/Ru4xfMU70qxwII4///////////ARAAGgw4NTE3MjU2MTQ4NjMiDLnfbZKzP0S6MJ9QsCqbArRNxHFRDnmXo2RH+PS6ZLHprUy+5dgrs/8u5zeNqVCK15B7v2af61uCyBQPCNKF8XzHri2XfTCJeitYdvxGBsg/bapReSMJD/X9UksdwoNY1+8ui/ZTfB9gwINGgOAsxkMhRgjIwfTlhxv51aTsMducnh5ZPSx9z0tmUjX/zoImJRPgIg3uLSpjKyNsFag6kGNf6w5Os6EAZTmeK085sO1/Wh8A6Pfr2uXbV7SNB8o5uc4iSp3t573djeTk0xN47nj4QJfdjrrJq+/WJbfaXWzT2+W8qTaWPxgkTSPqMsY3KL8qpi/1+4T4XqcmlZrwRNOw4PiAMhhW86biVqVnD3f+RoUleBFVS7pUDxfL5P/ywcE5VWvw4Z7OZ8Iwxr7oyQY6nQFES6yVgswn9qLccQ90jVAzJNp2X9RtvE/txxFD3SN1I7gdERQiaRFvt8p5h5yXE4jEeKTc0i/v+/TNRqmtDvlHLR6Yi1fVk0nTRPWyZB/65bl97aXnFLf2CpLngD5p/dBab0kxwOP0bTNQMmVuvqmSD1sN0H8HyFnzScI4zTrAOO4HgUn/CLSUFojfOIbDi5VC8Nn80tv0/ChWFS5/'
REGION_NAME = 'us-east-1' 
ACCOUNT_ID = "851725614863"

SOURCE_BUCKET = "polystudents3-tp4-1962292"
DEST_BUCKET   = "polystudents3-tp4-back-1962292"
REPLICATION_ROLE_NAME = "tp4-s3-replication-role"
TRAIL_NAME = "tp4-polystudents3-trail"


def ensure_destination_bucket(s3):
    """
    Create destination bucket if it does not exist and enable versioning.
    """
    print(f"[*] Ensuring destination bucket '{DEST_BUCKET}' exists and is versioned...")
    try:
        s3.head_bucket(Bucket=DEST_BUCKET)
        print(f"    Bucket {DEST_BUCKET} already exists (HeadBucket succeeded).")

    except ClientError as e:
        code = e.response["Error"]["Code"]
        print(f"    HeadBucket error code: {code}")

        if code in ("404", "NoSuchBucket", "NotFound"):
            print(f"    Bucket {DEST_BUCKET} does not exist, creating...")
            create_kwargs = {"Bucket": DEST_BUCKET}

            if REGION != "us-east-1":
                create_kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": REGION
                }
            s3.create_bucket(**create_kwargs)
        else:
            raise RuntimeError(
                f"Bucket name '{DEST_BUCKET}' is not usable (error {code}). "
                "Try another bucket name or check your AWS credentials/permissions."
            )

    s3.put_bucket_versioning(
        Bucket=DEST_BUCKET,
        VersioningConfiguration={"Status": "Enabled"}
    )
    print(f"    Versioning enabled on {DEST_BUCKET}.")

def get_replication_role_arn(session):
    """
    Use the same session (with explicit Lab credentials) to call STS.
    """
    sts = session.client("sts")
    identity = sts.get_caller_identity()
    account_id = identity["Account"]
    role_arn = f"arn:aws:iam::{account_id}:role/LabRole"
    print(f"[*] Using existing IAM role for replication: {role_arn}")
    return role_arn

def configure_replication(s3, role_arn):
    """
    Configure replication on the source bucket to the destination bucket.
    """
    print(f"[*] Enabling versioning on source bucket '{SOURCE_BUCKET}' (required for replication)...")
    s3.put_bucket_versioning(
        Bucket=SOURCE_BUCKET,
        VersioningConfiguration={"Status": "Enabled"}
    )

    print(f"[*] Configuring replication from '{SOURCE_BUCKET}' to '{DEST_BUCKET}'...")
    replication_config = {
        "Role": role_arn,
        "Rules": [
            {
                "ID": "ReplicateAllToBackup",
                "Status": "Enabled",
                "Priority": 1,
                "DeleteMarkerReplication": {"Status": "Enabled"},
                "Filter": {"Prefix": ""},  
                "Destination": {
                    "Bucket": f"arn:aws:s3:::{DEST_BUCKET}",
                    "StorageClass": "STANDARD"
                }
            }
        ]
    }

    s3.put_bucket_replication(
        Bucket=SOURCE_BUCKET,
        ReplicationConfiguration=replication_config
    )
    print("    Replication configuration applied.")


def create_or_update_cloudtrail_for_bucket(cloudtrail, s3):
    """
    Create a trail that logs write (modify/delete) S3 object events on SOURCE_BUCKET.
    Logs will be stored in DEST_BUCKET.
    """
    print(f"[*] Creating/Updating CloudTrail trail '{TRAIL_NAME}' for S3 object write events...")

    ensure_cloudtrail_bucket_policy(s3)

    try:
        cloudtrail.create_trail(
            Name=TRAIL_NAME,
            S3BucketName=DEST_BUCKET,
            IsMultiRegionTrail=False,
            IncludeGlobalServiceEvents=False
        )
        print(f"    Trail {TRAIL_NAME} created.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "TrailAlreadyExistsException":
            print(f"    Trail {TRAIL_NAME} already exists, updating settings...")
        else:
            raise

    cloudtrail.put_event_selectors(
        TrailName=TRAIL_NAME,
        EventSelectors=[
            {
                "ReadWriteType": "WriteOnly",
                "IncludeManagementEvents": False,
                "DataResources": [
                    {
                        "Type": "AWS::S3::Object",
                        "Values": [f"arn:aws:s3:::{SOURCE_BUCKET}/"]
                    }
                ]
            }
        ]
    )

    cloudtrail.start_logging(Name=TRAIL_NAME)
    print("    CloudTrail logging started (WriteOnly data events on S3 objects).")

def ensure_cloudtrail_bucket_policy(s3):
    """
    Ensure the destination bucket has the correct policy so CloudTrail
    can write logs into it.
    """
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSCloudTrailAclCheck",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:GetBucketAcl",
                "Resource": f"arn:aws:s3:::{DEST_BUCKET}"
            },
            {
                "Sid": "AWSCloudTrailWrite",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{DEST_BUCKET}/AWSLogs/{ACCOUNT_ID}/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            }
        ]
    }

    print(f"[*] Applying CloudTrail bucket policy on '{DEST_BUCKET}'...")
    s3.put_bucket_policy(
        Bucket=DEST_BUCKET,
        Policy=json.dumps(policy_doc)
    )
    print("    CloudTrail bucket policy applied.")


def print_proofs(s3, cloudtrail):
    """
    Print replication configuration and CloudTrail selectors as proof.
    """
    print("\n=== PROOF 1: Replication configuration on source bucket ===")
    try:
        rep = s3.get_bucket_replication(Bucket=SOURCE_BUCKET)
        print(json.dumps(rep["ReplicationConfiguration"], indent=2))
    except ClientError as e:
        print("Could not get replication configuration:", e)

    print("\n=== PROOF 2: CloudTrail configuration for the trail ===")
    try:
        desc = cloudtrail.describe_trails(trailNameList=[TRAIL_NAME])
        print("DescribeTrails:")
        print(json.dumps(desc["trailList"], indent=2))
    except ClientError as e:
        print("Could not describe trail:", e)

    try:
        selectors = cloudtrail.get_event_selectors(TrailName=TRAIL_NAME)
        print("\nEventSelectors:")
        print(json.dumps(selectors, indent=2))
    except ClientError as e:
        print("Could not get event selectors:", e)


def main():
    session = boto3.Session(
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=SESSION_TOKEN)

    s3 = session.client("s3")
    cloudtrail = session.client("cloudtrail")

    ensure_destination_bucket(s3)

    role_arn = get_replication_role_arn(session)
    configure_replication(s3, role_arn)

    create_or_update_cloudtrail_for_bucket(cloudtrail, s3)

    print_proofs(s3, cloudtrail)


if __name__ == "__main__":
    main()
