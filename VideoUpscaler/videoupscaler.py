import cv2
import os
import boto3
import json
import logging
import base64
import io
import concurrent.futures
import functools
from PIL import Image
logging.basicConfig(level=logging.INFO)

class VideoUpscaler:
    def __init__(self):
        self.s3client = boto3.client('s3')

    def getNewDim(self, image, config):
        height, width = image.shape[:2]
        aspect_ratio = width / height
        new_width = int(width / 4)
        new_height = int(new_width / aspect_ratio)
        logging.debug(f"New width: {new_width} and New height: {new_height} and aspect ratio: {aspect_ratio}")
        if new_width > config['max_size']:
            logging.debug(f"Width too large.")
            new_width = config['max_size']
            new_height = int(new_width / aspect_ratio)
        elif new_height > config['max_size']:
            logging.debug("Height too large.")
            new_height = config['max_size']
            new_width = int(new_height * aspect_ratio)
        elif new_width < config['min_size']:
            logging.debug("Width too small.")
            new_width =  config['min_size']
            new_height = int(new_width / aspect_ratio)
        elif new_height <  config['min_size']:
            logging.debug("Height too small.")
            new_height =  config['min_size']
            new_width = int(new_height * aspect_ratio)
        logging.debug(f"Returning New width: {new_width} and New height: {new_height}")
        return new_width, new_height

    def breakDownFrames(self,id,video,config):
        logging.info(f"Breaking down frames from video {video} for video id: {id}")
        try:
            os.makedirs(f"/tmp/{id}/oldframes")
        except:
            pass

        if "s3://" in video:
            bucket, key = video.split('/',2)[-1].split('/',1)
            filename = key.split("/")[-1]
            video = f"/tmp/{id}/{filename}"
            self.s3client.download_file(bucket, key, video)
        vidcap = cv2.VideoCapture(video)
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        success,image = vidcap.read()
        count = 0
        new_width = None
        new_height = None
        while success:
            success, image = vidcap.read() 
            try:
                if not new_width or not new_height:
                    new_width, new_height = self.getNewDim(image,config)
                resize = cv2.resize(image, (new_width, new_height)) 
                cv2.imwrite(f"/tmp/{id}/oldframes/%04d.jpg" % count, resize) 
                if cv2.waitKey(10) == 27: 
                    break
                count += 1
            except AttributeError:
                pass
            except Exception as e:
                print(e)
        return fps

    def createVideoFromFrames(self,id,source,output,fps):
        logging.info(f"Creating video ({fps} fps) from frames in {source} to {output} for video id: {id}")
        try:
            img = Image.open(f"{source}/0000.jpg")
            width = img.width 
            height = img.height 
        except:
            logging.info("No frames found.")
            return
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(f"{output}",fourcc, fps, (width,height))
        images = [img for img in os.listdir(f"{source}/") if img.endswith(".jpg")]
        images.sort()

        img_array = []
        for filename in images:
            img = cv2.imread(os.path.join(f"{source}/", filename))
            # img_array.append(img)
            out.write(img)
        out.release()

    def query_endpoint_with_json_payload(self, payload, contentType, accept, endpoint):
        logging.info("Starting the Sagemaker Query")
        encoded_payload = json.dumps(payload).encode('utf-8')
        sageMakerClient = boto3.client('runtime.sagemaker')
        response = sageMakerClient.invoke_endpoint(
            EndpointName= endpoint,
            ContentType= contentType,
            Body= encoded_payload,
            Accept= accept
        )
        return response

    @staticmethod
    def parse_response(query_response):
        response_dict = json.loads(query_response['Body'].read())
        return response_dict['generated_images'], response_dict['prompt']

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
    def imageToString(image):
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
        return img_str


    def upscale_image(self,base64_string,endpoint):
        requestType = 'application/json;jpeg'
        encoded_image = base64_string
        payload = {
            "image": encoded_image,
            "prompt": "",
            "num_inference_steps":50,
            "guidance_scale":7.5
        }
        try:
            response = self.query_endpoint_with_json_payload( payload, requestType, requestType, endpoint)
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
    
    def upscale_image_file(self,id,endpoint,filename):
        image_data = open(os.path.join(f"/tmp/{id}/oldframes/", filename), "rb")
        image_string = base64.b64encode(image_data.read()).decode('utf-8')
        upscaled_image_string = self.upscale_image(image_string,endpoint)
        with open(f"/tmp/{id}/newframes/{filename}", "wb") as fh:
            fh.write(base64.decodebytes(upscaled_image_string.encode('utf-8')))

    def upscaleFrames(self,id,config):
        logging.info(f"Upscaling frames for video id: {id}")
        try:
            os.makedirs(f"/tmp/{id}/newframes")
        except:
            pass

        images = [img for img in os.listdir(f"/tmp/{id}/oldframes/") if img.endswith(".jpg")]
        images.sort()

        with concurrent.futures.ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
            executor.map(functools.partial(self.upscale_image_file, id, config['endpoint']), images)