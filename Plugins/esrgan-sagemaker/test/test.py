import boto3
import json
import base64
import io
from PIL import Image

endpoint = "<ENDPOINT NAME>"

def parse_response(query_response):
    response_dict = json.loads(query_response['Body'].read())
    return response_dict['generated_images'], response_dict['prompt']

def decode_images(generated_images):
    """Decode the images and convert to RGB format and return"""
    imageArr = []
    for generated_image in generated_images:
        generated_image_decoded = io.BytesIO(base64.b64decode(generated_image.encode()))
        generated_image_rgb = Image.open(generated_image_decoded).convert("RGB")
        imageArr.append(generated_image_rgb)
    return imageArr

def query_endpoint_with_json_payload(endpoint, payload, contentType, accept):
    print("Starting the Sagemaker Query")
    encoded_payload = json.dumps(payload).encode('utf-8')
    sageMakerClient = boto3.client('runtime.sagemaker')
    response = sageMakerClient.invoke_endpoint(
        EndpointName= endpoint,
        ContentType= contentType,
        Body= encoded_payload,
        Accept= accept
    )
    return response

def imageToString(image):
    # buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    #img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
    #return img_str

image_path = "./SD/frames/0001.png"

try: 
    encoded_image = ""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')
    requestType = 'application/json'
    payload = {
        "image": encoded_image
    }
    
    response = query_endpoint_with_json_payload(endpoint, payload, requestType, requestType)
    encoded_images, prompt = parse_response(response)
    decoded_images = decode_images(encoded_images)
    decoded_images[0].save("./test.jpg", format="JPEG")
except FileNotFoundError:
    print(f"File {image_path} not found.")

