"""
File: JumpStartRTUpscale.py
Description: This file contains the implemented child class for the UpscaleProvider.
This child class uses a SageMaker Real Time endpoint backed by the JumpStart Stable Diffusion
Model. This class requires both the RT endpoint and S3 bucket to be defined.
The RT endpoint is the endpoint that is used to upscale the images. The S3 bucket is used to store
the images. 

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    The purpose of this file is implement a way to upscale images. This particular class implements
    the SageMaker JumpStart Real Time endpoint. Note that any RealTime endpoint would also work using 
    this class as long as the model that backs the endpoint still uses base64 in the same manner. 
"""
import io
import os
import boto3
import base64
from PIL import Image
import json
from UpscaleInterface import UpscaleProvider
import logging
logging.basicConfig(level=logging.INFO)
# For local test with .env file with AWS user credentials 
# from dotenv import load_dotenv
# load_dotenv(dotenv_path = 'secrets.env')
# endpoint = "upscaleEndpoint"

# Child class of UpscaleProvider
class JumpStartRTUpscaleProvider(UpscaleProvider):
    def __init__(self, s3_bucket: str, endpoint: str) -> None:
        self.s3_bucket_name = s3_bucket
        self.endpoint = endpoint
  
    # Static methods are used to define utility functions that can be used without creating an instance of the class.
    @staticmethod 
    def decode_images(generated_images):
        """Decode the images and convert to RGB format and return"""
        imageArr = []
        for generated_image in generated_images:
            generated_image_decoded = io.BytesIO(base64.b64decode(generated_image.encode()))
            generated_image_rgb = Image.open(generated_image_decoded).convert("RGB")
            imageArr.append(generated_image_rgb)
        return imageArr

    @staticmethod
    def parse_response(query_response):
        response_dict = json.loads(query_response['Body'].read())
        return response_dict['generated_images'], response_dict['prompt']
    
    @staticmethod
    def imageToString(image):
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
        return img_str
    
    # Class dependant methods, mostly works with class attributes
    def setS3_key(self, s3_key:str):
        self.s3_key = s3_key
    
    def query_endpoint_with_json_payload(self, payload, contentType, accept):
        logging.info("starting the Sagemaker Query")
        encoded_payload = json.dumps(payload).encode('utf-8')
        sageMakerClient = boto3.client('runtime.sagemaker')
        response = sageMakerClient.invoke_endpoint(
            EndpointName= self.endpoint,
            ContentType= contentType,
            Body= encoded_payload,
            Accept= accept
        )
        return response
    
    # Interface Implementation
    def upscale_image(self, base64_string):
        requestType = 'application/json;jpeg'
        encoded_image = base64_string
        payload = {
            "image": encoded_image,
            "prompt": "",
            "num_inference_steps":50,
            "guidance_scale":7.5
        }
        try:
            response = self.query_endpoint_with_json_payload( payload, requestType, requestType)
            logging.info("response is: ")
            logging.info(str(response))
            encoded_images, prompt = self.parse_response(response)
            decoded_images = self.decode_images(encoded_images)
            imageString = self.imageToString(decoded_images[0]) 
            logging.info("imageString is: ")
            return imageString
        except Exception as e:
            logging.info("failed to upscale with: ")
            logging.info(str(e))
            return None
    
    def send_and_downscale(self, base64_image: str) -> str:
        try:
            image = Image.open(io.BytesIO(base64_image))
        except Exception as e:
            print(f"Error opening image: {e}")
            logging.info("cannot open ")
            return None
        logging.info("image opened")

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
        logging.info("new height is: ")
        logging.info(str(new_height))
        logging.info("new width is: ")
        logging.info(str(new_width))
        resized_image = image.resize((new_width, new_height))
        resized_image_bytes = io.BytesIO()
        logging.info("image resized, with format")
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
            logging.info("image uploaded to S3")
            status = ("image uploaded to S3")
        except Exception as e:
            status = (f"Error uploading image to S3: {e}")
            logging.info("cannot upload to S3")
            return status
        return status
    
    def retrieve_and_upscale(self, key: str) -> str:
        self.s3_key = key
        s3_client = boto3.client('s3')
        try:
            logging.info("key is: ")
            logging.info(str(key))
            logging.info("Bucket is: ")
            logging.info(str(self.s3_bucket_name))
            logging.info("endpoint is: ")
            logging.info(str(self.endpoint))
            s3_object = s3_client.get_object(Bucket=self.s3_bucket_name, Key=key)
            logging.info("s3_object is: ")
            logging.info(str(s3_object))
            image_data = s3_object['Body'].read()
            logging.info("image_data is: ")
            logging.info(str(image_data))
            # convert the image to a base64 string for Jpegs
            # file_extension = key.split(".")[-1]
            # if file_extension.lower() == "png":
            #     image = Image.open(io.BytesIO(image_data))
                
            #     buffered = io.BytesIO()
            #     image.convert('RGB').save(buffered, format="JPEG")
            #     image_data = buffered.getvalue()
            #     logging.info("image_data converted")
            

            base64_string = base64.b64encode(image_data).decode('utf-8')
            print("Length of string is: ")
            print(len(base64_string))
            upscaled_image = self.upscale_image(base64_string)
            if(upscaled_image == None):
                return "upscale failed"
            return upscaled_image
        except Exception as e:
            logging.info("Unable to upscale image" + str(e))
            return "Unable to upscale image"
    
