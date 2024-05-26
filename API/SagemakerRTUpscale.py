"""
File: SagemakerRTUpscale.py
Description: This file contains the implemented child class for the UpscaleProvider.
This child class uses a SageMaker Real Time endpoint backed by the Sagemaker Stable Diffusion
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
    the SageMaker Sagemaker Real Time endpoint. Note that any RealTime endpoint would also work using 
    this class as long as the model that backs the endpoint still uses base64 in the same manner. 
"""
import io
import os
import boto3
import base64
from PIL import Image
import json
from S3CommonUpscaler import S3CommonUpscaler
import logging
logging.basicConfig(level=logging.INFO)
# For local test with .env file with AWS user credentials 
from dotenv import load_dotenv
load_dotenv(dotenv_path = 'secrets.env')

# Child class of S3CommonUpscaler
class SagemakerRTUpscaleProvider(S3CommonUpscaler):

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
    
    def query_endpoint_with_json_payload(self, payload, contentType, accept):
        logging.info("Starting the Sagemaker Query")
        encoded_payload = json.dumps(payload).encode('utf-8')
        sageMakerClient = boto3.client('runtime.sagemaker')
        response = sageMakerClient.invoke_endpoint(
            EndpointName= self.endpoint,
            ContentType= contentType,
            Body= encoded_payload,
            Accept= accept
        )
        return response
    
    # Class Implementation
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
            logging.info("Response is: ")
            logging.info(str(response))
            encoded_images, prompt = self.parse_response(response)
            decoded_images = self.decode_images(encoded_images)
            imageString = self.imageToString(decoded_images[0]) 
            logging.info("ImageString is: ")
            return imageString
        except Exception as e:
            logging.info("Failed to upscale with: ")
            logging.info(str(e))
            return None
    
    def retrieve_and_upscale(self, key: str) -> str:
        self.s3_key = key
        s3_client = boto3.client('s3')
        try:
            logging.info("Key is: ")
            logging.info(str(key))
            logging.info("Bucket is: ")
            logging.info(str(self.s3_bucket_name))
            logging.info("Endpoint is: ")
            logging.info(str(self.endpoint))
            s3_object = s3_client.get_object(Bucket=self.s3_bucket_name, Key=key)
            logging.info("S3_object is: ")
            logging.info(str(s3_object))
            image_data = s3_object['Body'].read()
            logging.info("Image_data is: ")
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
                return "Upscale failed"
            return upscaled_image
        except Exception as e:
            logging.info("Unable to upscale image" + str(e))
            return "Unable to upscale image"