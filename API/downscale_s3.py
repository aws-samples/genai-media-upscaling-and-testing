"""
File: downscale_s3.py
Description: This file contains the implementation of the SagemakerRTUpscale class to 
downscale an image and then store it in an S3 bucket. This class is also responsible for 
retrieving the down scaled image form the S3 bucket and then upscaling it sending it back
to the requester. 

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    The purpose of this file is to have all of the relevant methods that back the API. 
"""
import json
from SagemakerRTUpscale import SagemakerRTUpscaleProvider
from flask import jsonify
# API Receiver
def disect_request_retrieve(request):
    try:
        s3_key = request.args.get('s3_key')
        s3_bucket = request.args.get('s3_bucket')
        endpoint = request.args.get('endpoint')
        try: 
            print("trying")
            image_data = sageMakerRetrieveUpscale(s3_bucket=s3_bucket, endpoint=endpoint, s3_key=s3_key)
            return {'data': image_data, 'code': 200}
        except Exception as e:
            data = ("Unable to retrieve image" + str(e))
            return {'data': data, 'code': 400}
            
    except Exception as e:
        data = ("Unable to dissect request" + str(e))
        return {'data': data, 'code': 300}

# Provider execution 
def sageMakerRetrieveUpscale(s3_bucket:str, endpoint: str, s3_key:str):
    # try to create and configure the SagemakerRTUpscaleProvider
    try: 
        # create and configure the provider
        sageMakerRT = SagemakerRTUpscaleProvider(s3_bucket)
        sageMakerRT.setS3_key(s3_key)
    except Exception as e:
        return 'error: create JT class object' + str(e)
    
    try:
        image_data = sageMakerRT.retrieve_and_upscale(s3_key)
        return image_data
    except Exception as e:
        return 'error: retrieve image and upscale' + str(e)
    
def disect_request_retrieve_video(request):
    try:
        s3_key = request.args.get('s3_key')
        s3_bucket = request.args.get('s3_bucket')
        endpoint = request.args.get('endpoint')
        max_workers = request.args.get('max_workers')

        try: 
            print(f"Received request: {request.args}")
            jobid = sageMakerRetrieveUpscaleVideo(s3_bucket=s3_bucket, endpoint=endpoint, max_workers=max_workers, s3_key=s3_key)
            return {'data': jobid, 'code': 200}
        except Exception as e:
            data = ("Unable to retrieve video" + str(e))
            return {'data': data, 'code': 400}
            
    except Exception as e:
        data = ("Unable to dissect request" + str(e))
        return {'data': data, 'code': 300}

def sageMakerRetrieveUpscaleVideo(s3_bucket:str, endpoint: str, max_workers: int, s3_key:str):
    # try to create and configure the SagemakerRTUpscaleProvider
    try: 
        # create and configure the provider
        sageMakerRT = SagemakerRTUpscaleProvider(s3_bucket)
        sageMakerRT.setS3_key(s3_key)
    except Exception as e:
        return 'error: create JT class object' + str(e)
    
    try:
        jobid = sageMakerRT.retrieve_and_upscale_video(s3_key, endpoint, max_workers)
        return jobid
    except Exception as e:
        return 'error: retrieve video and upscale' + str(e)

def disect_request_store(request):
    data = request.get_json()
    print(data)
    base64_string = data['image']
    image_data = SagemakerRTUpscaleProvider.decode_base64_to_image(base64_string)    
    s3_key_name = data['s3_key_name']
    s3_bucket = data['s3_bucket']

    upscaleMethod = data['upscaleMethod']
    
    # if upscaleMethod is the SagemakerClass
    if upscaleMethod == "sageMakerRT":
        endpoint = data['endpoint']
        # try to downscale and store the image
        try: 
            id = sageMakerDownscaleStore(s3_bucket=s3_bucket, endpoint=endpoint, s3_key=s3_key_name, image_data=image_data)                
            return {'data': id,'code': 200}
        except Exception as e:
            print("Unable to store image" + str(e))
            return {'data': 'Unable to store image', 'code': 500}
    else:
        return {'data': 'Upscale Method not yet implemented', 'code': 400}

def sageMakerDownscaleStore(s3_bucket:str, endpoint:str, s3_key:str, image_data:str):
    try:
        # create class implementation
        sageMakerRT = SagemakerRTUpscaleProvider(s3_bucket)
        # set the params from API call for image storage. 
        sageMakerRT.setS3_key(s3_key)
    except Exception as e:
        print("Unable to create JT class object:" + str(e))
        return 'error: create JT class object'+ str(e)
    try:
        returnMsg = sageMakerRT.send_and_downscale(image_data)
        return returnMsg
    except Exception as e:
        return 'error: send and downscale: ' + str(e)
    
def disect_request_store_video(request):
    data = request.get_json()
    print(data)
    s3_key_name = data['s3_key_name']
    s3_bucket = data['s3_bucket']
    min_size = data['min_size']
    max_size = data['max_size']
    # try to downscale and store the video
    try: 
        id = sageMakerDownscaleStoreVideo(s3_bucket=s3_bucket, min_size=min_size, max_size=max_size, s3_key=s3_key_name)                
        return {'data': id,'code': 200}
    except Exception as e:
        print("Unable to store video" + str(e))
        return {'data': 'Unable to store video', 'code': 500}
    
def sageMakerDownscaleStoreVideo(s3_bucket:str, min_size:int, max_size:int, s3_key:str):
    try:
        # create class implementation
        sageMakerRT = SagemakerRTUpscaleProvider(s3_bucket)
        # set the params from API call for video storage. 
        sageMakerRT.setS3_key(s3_key)
    except Exception as e:
        print("Unable to create Sagemaker class object:" + str(e))
        return 'error: create Sagemaker class object'+ str(e)
    try:
        returnMsg = sageMakerRT.send_and_downscale_video(s3_key, min_size, max_size)
        return returnMsg
    except Exception as e:
        return 'error: send and downscale: ' + str(e)
    
def disect_request_get_video_status(request):
    try:
        id = request.args.get('id')
    except Exception as e:
        data = ("Unable to dissect request" + str(e))
        return {'data': data, 'code': 300}
    
    try: 
        sageMakerRT = SagemakerRTUpscaleProvider("")
    except Exception as e:
        return {'data': 'Unable to create JT class object' + str(e), 'code': 500}
    try:
        returnMsg = sageMakerRT.get_video_status(id)
        item = json.loads(returnMsg)
        returnDict = {}
        returnDict["output"] = item.get("output",{}).get("S")
        returnDict["status"] = item.get("status",{}).get("S")
        return {'data': json.dumps(returnDict), 'code': 200}
    except Exception as e:
        return {'data': 'Unable to get video status: ' + str(e), 'code': 500}
    
    