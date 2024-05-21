"""
File: UpscaleInterface.py
Description: This file contains the Interface and Parent Class for Upscaling. 
The interface defines what the class must implement. 
The Parent class enforces that implementation and also defines some relevant static methods

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    The purpose of this file is to define the interface and parent class for upscaling.
    Any extension to the Upscaler that implements a different upscaling method needs to
    implement the UpscaleInterface and UpscaleProvider classes.
    The UpscaleProvider class is the parent class that enforces implementation. 
"""
import base64
import io
from  PIL import Image
import abc

# Interface
class UpscaleInterfaceMeta(abc.ABCMeta):

    @abc.abstractmethod
    def upscale_image(self, img:str) -> str:
        # receive an image and upscale it as a base64 string
        # Return the base64 encoded image.
        pass

    @abc.abstractmethod
    def upscale_video(self, s3_bucket:str, s3_key:str) -> str:
        # receive an s3 bucket and key of a video and upscale it.
        # Return a job id.
        pass

# Concrete Parent Class
class UpscaleProvider(metaclass=UpscaleInterfaceMeta):
    def __init__(self, upscale_model):
        self.upscale_model = upscale_model

    @staticmethod
    def decode_base64_to_image(encoded_image:str) -> str:
        decoded_image = base64.b64decode(encoded_image)
        return decoded_image
    
    @staticmethod
    def encode_image_to_base64(image:Image) -> str:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")