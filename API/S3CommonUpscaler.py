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
import boto3
from PIL import Image
from UpscaleInterface import UpscaleProvider
import logging
logging.basicConfig(level=logging.INFO)

# Child class of UpscaleProvider
class S3CommonUpscaler(UpscaleProvider):
    def __init__(self, s3_bucket: str, endpoint: str) -> None:
        self.s3_bucket_name = s3_bucket

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
    
    def send_and_downscale_video(self, s3_bucket: str, s3_key: str) -> str:
        pass