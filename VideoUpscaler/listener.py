import boto3
import os
import shutil
from sqs_listener import SqsListener
from videoupscaler import VideoUpscaler
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

class VideoUpscaleJobListener(SqsListener):
    def __init__(self, queue, **kwds):
        super().__init__(queue, **kwds)
        self.s3client = boto3.client('s3')
        self.VideoUpscaler = VideoUpscaler()     

    def handle_message(self, body, attributes, messages_attributes):
        logging.info(f"Received message: {body}")
        id = body['id']
        video = body['video']
        method = body['method']
        config = {}
        config['endpoint'] = body['endpoint']
        config['min_size'] = int(body['min_size'])
        config['max_size'] = int(body['max_size'])
        config['max_workers'] = int(body['max_workers'])
        bucket, key = video.split('/',2)[-1].split('/',1)
        filename = video.split("/")[-1]
        filenameNoExt = filename.split(".")[0]
        keyNoExt = os.path.splitext(key)[0]
        prefix = None
        if method == "upscale":
            fps = self.VideoUpscaler.breakDownFrames(id, video, config)
            self.VideoUpscaler.upscaleFrames(id, config)
            prefix = "upscaled"
            self.VideoUpscaler.createVideoFromFrames(id,f"/tmp/{id}/newframes",f"/tmp/{id}/{filenameNoExt}-{prefix}.mp4",fps)
        elif method == "downscale":
            fps = self.VideoUpscaler.breakDownFrames(id, video, config)
            prefix = "downscaled"
            self.VideoUpscaler.createVideoFromFrames(id,f"/tmp/{id}/oldframes",f"/tmp/{id}/{filenameNoExt}-{prefix}.mp4",fps)
        if prefix:
            logging.info(f"Uploading video: /tmp/{id}/{filenameNoExt}-{prefix}.mp4")
            self.s3client.upload_file(f"/tmp/{id}/{filenameNoExt}-{prefix}.mp4", bucket, f"{keyNoExt}-{prefix}.mp4")
            shutil.rmtree(f"/tmp/{id}")

session = boto3.session.Session()
region = session.region_name

listener = VideoUpscaleJobListener(os.environ.get('SQS_QUEUE'), region_name=region)
listener.listen()