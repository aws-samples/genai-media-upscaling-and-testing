"""
File: downscale_s3.py
Description: This file contains the implementation of the JumpStartRTUpscale class to 
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
from JumpStartRTUpscale import JumpStartRTUpscaleProvider
from flask import jsonify
# API Receiver
def disect_request_retrieve(request):
    try:
        s3_key = request.args.get('s3_key')
        s3_bucket = request.args.get('s3_bucket')
        endpoint = request.args.get('endpoint')
        try: 
            print("trying")
            image_data = jumpStartRetrieveUpscale(s3_bucket=s3_bucket, endpoint=endpoint, s3_key=s3_key)
            return {'data': image_data, 'code': 200}
        except Exception as e:
            data = ("Unable to retrieve image" + str(e))
            return {'data': data, 'code': 400}
            
    except Exception as e:
        data = ("Unable to dissect request" + str(e))
        return {'data': data, 'code': 300}

# Provider execution 
def jumpStartRetrieveUpscale(s3_bucket:str, endpoint: str, s3_key:str):
    # try to create and configure the JumpStartRTUpscaleProvider
    try: 
        # create and configure the provider
        stableDiff = JumpStartRTUpscaleProvider(s3_bucket, endpoint)
        stableDiff.setS3_key(s3_key)
    except Exception as e:
        return 'error: create JT class object' + str(e)
    
    try:
        image_data = stableDiff.retrieve_and_upscale(s3_key)
        return image_data
    except Exception as e:
        return 'error: retrieve image and upscale' + str(e)

def disect_request_store(request):
    data = request.get_json()
    print(data)
    base64_string = data['image']
    image_data = JumpStartRTUpscaleProvider.decode_base64_to_image(base64_string)    
    s3_key_name = data['s3_key_name']
    s3_bucket = data['s3_bucket']

    upscaleMethod = data['upscaleMethod']
    
    # if upscaleMethod is the JumpStartClass
    if upscaleMethod == "stableDiffusionJT":
        endpoint = data['endpoint']
        # try to downscale and store the image
        try: 
            status = jumpStartDownscaleStore(s3_bucket=s3_bucket, endpoint=endpoint, s3_key=s3_key_name, image_data=image_data)                
            return {'data': status,'code': 200}
        except Exception as e:
            print("Unable to store image" + str(e))
            return {'data': 'Unable to store image', 'code': 500}
    else:
        return {'data': 'Upscale Method not yet implemented', 'code': 400}

def jumpStartDownscaleStore(s3_bucket:str, endpoint:str, s3_key:str, image_data:str):
    try:
        # create class implementation
        stableDiff = JumpStartRTUpscaleProvider(s3_bucket, endpoint)
        # set the params from API call for image storage. 
        stableDiff.setS3_key(s3_key)
    except Exception as e:
        print("Unable to create JT class object:" + str(e))
        return 'error: create JT class object'+ str(e)
    try:
        returnMsg = stableDiff.send_and_downscale(image_data)
        return returnMsg
    except Exception as e:
        return 'error: send and downscale' + str(e)


    