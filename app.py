import datetime
import time
import boto3
import json
import uuid
import os

KEY_ID = os.getenv("KEY_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
LOG_REGION = os.getenv("LOG_REGION")

logs = boto3.client("logs", aws_access_key_id=KEY_ID, aws_secret_access_key=ACCESS_KEY, region_name=LOG_REGION)

def get_container_id():
    """현재 실행 중인 컨테이너 ID 가져오기"""
    try:
        with open("/proc/self/cgroup", "r") as f:
            for line in f:
                if "docker" in line or "sandbox" in line:
                    return line.strip().split("/")[-1]  # 컨테이너 ID 부분 추출
    except Exception as e:
        print(f"Error getting container ID: {e}")
    return "unknown-container"

def logging(context=None):
    LOG_GROUP = "/wsi/Logging/access/"
    LOG_STREAM = context.log_stream_name if context else f"log-stream-{uuid.uuid4()}"

    container_id = get_container_id()

    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass

    try:
        logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass

    timestamp = int(round(time.time() * 1000))
    now = datetime.datetime.now()

    log_message = f"{now.strftime('%Y-%m-%d %H:%M:%S')} [Container: {container_id}] Application Running!"

    response = logs.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=LOG_STREAM,
        logEvents=[{"timestamp": timestamp, "message": log_message}]
    )
    return response

def lambda_handler(event, context):
    result = logging(context)
    return json.dumps({"StatusCode": result['ResponseMetadata']['HTTPStatusCode']})