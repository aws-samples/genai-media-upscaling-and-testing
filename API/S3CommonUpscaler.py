"""
File: S3CommonUpscaler.py
Description: This file contains the implemented child class for the UpscaleProvider.
This child class provides a common class to implement the S3 downscale method.

Author: @bainskb
Contributors: @bainskb, @andklee

Date Created: 05/10/2024
Version: 1.0

References: N/A

Purpose:
    The purpose of this file is implement a way to upscale images. This particular class implements
    the S3 downscale method. 
"""
import io
import os
import uuid
import json
import boto3
from PIL import Image
from UpscaleInterface import UpscaleProvider
import logging
logging.basicConfig(level=logging.INFO)

# Child class of UpscaleProvider
class S3CommonUpscaler(UpscaleProvider):
    def __init__(self, s3_bucket: str) -> None:
        self.s3_bucket_name = s3_bucket
        self.sqs_queue_url = os.getenv('SQS_QUEUE_URL')
        self.ddb_table = os.getenv('DDB_TABLE')

    # Class dependant methods, mostly works with class attributes
    def setS3_key(self, s3_key:str):
        self.s3_key = s3_key

    def send_and_downscale(self, base64_image: str) -> str:
        try:
            image = Image.open(io.BytesIO(base64_image))
        except Exception as e:
            logging.info(f"Error opening image: {e}")
            logging.info("Cannot open ")
            return None
        logging.info("Image opened")

        MIN_SIZE = 100
        MAX_SIZE = 200

        width, height = image.size
        aspect_ratio = width / height

        if width > MAX_SIZE:
            new_width = MAX_SIZE
            new_height = int(new_width / aspect_ratio)
        elif height > MAX_SIZE:
            new_height = MAX_SIZE
            new_width = int(new_height * aspect_ratio)
        elif width < MIN_SIZE:
            new_width = MIN_SIZE
            new_height = int(new_width / aspect_ratio)
        elif height < MIN_SIZE:
            new_height = MIN_SIZE
            new_width = int(new_height * aspect_ratio)
        else:
            logging.debug("ELSE FAIL!!!")
            new_width = MAX_SIZE
            new_height = MAX_SIZE
        
        #  Downscale the Image
        logging.info("New height is: ")
        logging.info(str(new_height))
        logging.info("New width is: ")
        logging.info(str(new_width))
        resized_image = image.resize((new_width, new_height))
        resized_image_bytes = io.BytesIO()
        logging.info("image resized, with format ")
        file_format = str(image.format)
        logging.info(file_format)

        content_type_mapping = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "JPG": "image/jpeg",
        }
        content_type = content_type_mapping.get(file_format, "application/octet-stream")
        resized_image.save(resized_image_bytes, format=file_format)

        
        s3_client = boto3.client('s3') 
        status = ("image attempt")
        try:
            s3_client.put_object(Body=resized_image_bytes.getvalue(), Bucket=self.s3_bucket_name, Key=self.s3_key, ContentType=content_type)
            logging.info("Image uploaded to S3")
            status = ("image uploaded to S3")
        except Exception as e:
            status = (f"Error uploading image to S3: {e}")
            logging.info("cannot upload to S3")
            return status
        return status
    
    def send_and_downscale_video(self, key: str, min_size: int, max_size: int) -> str:
        idToCreate = uuid.uuid4()
        sqs_client = boto3.client('sqs')
        ddb_client = boto3.client('dynamodb')
        body = {
            "id":str(idToCreate),
            "video":f"s3://{self.s3_bucket_name}/{key}",
            "endpoint": "None",
            "min_size": min_size,
            "max_size": max_size,
            "max_workers": 1,
            "method": "downscale"
        }
        sqs_client.send_message(
            QueueUrl=self.sqs_queue_url,
            MessageBody=json.dumps(body)
        )
        ddb_client.put_item(
            TableName=self.ddb_table,
            Item={
                'id': {
                    'S': str(idToCreate)
                },
                'video': {
                    'S': f"s3://{self.s3_bucket_name}/{key}"
                },
                'min_size': {
                    'N': str(min_size)
                },
                'max_size': {
                    'N': str(max_size)
                },
                'method': {
                    'S': "downscale"
                },
                'status': {
                    'S': "Submitted"
                }
            }
        )

        return str(idToCreate)

    def retrieve_and_upscale_video(self, key: str, endpoint: str, max_workers: int) -> str:
        idToCreate = uuid.uuid4()
        sqs_client = boto3.client('sqs')
        ddb_client = boto3.client('dynamodb')
        body = {
            "id":str(idToCreate),
            "video":f"s3://{self.s3_bucket_name}/{key}",
            "endpoint": endpoint,
            "min_size": 1,
            "max_size": 1,
            "max_workers": max_workers,
            "method": "upscale"
        }
        sqs_client.send_message(
            QueueUrl=self.sqs_queue_url,
            MessageBody=json.dumps(body)
        )
        ddb_client.put_item(
            TableName=self.ddb_table,
            Item={
                'id': {
                    'S': str(idToCreate)
                },
                'video': {
                    'S': f"s3://{self.s3_bucket_name}/{key}"
                },
                'endpoint': {
                    'S': endpoint
                },
                'max_workers': {
                    'N': str(max_workers)
                },
                'method': {
                    'S': "upscale"
                },
                'status': {
                    'S': "Submitted"
                }
            }
        )
        return str(idToCreate)
    
    def get_video_status(self, id: str) -> str:
        ddb_client = boto3.client('dynamodb')
        item = ddb_client.get_item(
            TableName=self.ddb_table,
            Key={
                'id': {
                    'S': str(id)
                }
            },
        )
        return json.dumps(item['Item'])