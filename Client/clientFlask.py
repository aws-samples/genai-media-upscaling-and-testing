"""
File: clientFlask.py
Description: This is sample Client to interact with the Flask API hosted on EKS deployed by the CDK

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    This file is used to test the api and send images to the api.
    It is also used to test the api and retrieve images from the api.
"""
import requests
import base64

def send_image_to_api(image_path, api_url, s3_bucket, s3Key, endpoint):
    try: 
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
    except FileNotFoundError:
        print(f"File {image_path} not found.")
        return
        
    
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    data = {'image': encoded_image, "s3_bucket":s3_bucket, "s3_key_name": s3Key, "endpoint":endpoint, 'upscaleMethod': "stableDiffusionJT"}

    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url+'/store', headers=headers, json=data, verify=True)

    return response.json()

# will send the s3_key as an query parameter argument
def retrieve_image_from_api(api_url, s3_bucket, endpoint, s3_key):
    url = f"{api_url}/retrieve?s3_key={s3_key}&s3_bucket={s3_bucket}&endpoint={endpoint}"
    response = requests.get(url, verify=True)
    return response.json()
    

if __name__ == '__main__':
    
    # local_url = "https://7FF3AFB6436499EA6CA228F872972DE6.gr7.us-west-2.eks.amazonaws.com"
    # the URL of the api is the elb front of the cluster
    # api_url = 'https://k8s-upscale-upscale-95edc3b7b7-2f89f38623a7c96c.elb.us-west-2.amazonaws.com'
    api_url = "http://127.0.0.1:5000"
    # secure_api_url = "https://127.0.0.1:5000"
    # api_url = secure_api_url
    
    # bucket and end points are the names of the endpoint and the bucket and NOT ARN
    s3_bucket = ""
    endpoint = "upscaleEndpoint"
    image_path = '../Resources/SampleImages/Real/NataliePortman.jpg'
    s3_key = "NataliePortman.jpg"

    response = send_image_to_api(image_path=image_path, api_url=api_url, s3_bucket=s3_bucket, s3Key=s3_key, endpoint=endpoint)
    print(response)
    response = retrieve_image_from_api(api_url=api_url, s3_bucket=s3_bucket, s3_key=s3_key, endpoint=endpoint)
    print(response)
    
    if response[1] == 200:
        image_data = response[0]['data']
        image_data = base64.b64decode(image_data)
        with open('new_image.jpg', 'wb') as f:
            f.write(image_data)
    else:
        print(response[0]['error'])



    