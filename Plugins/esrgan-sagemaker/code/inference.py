import torch
import torch.nn as nn
import json
from pathlib import Path
import numpy as np
import cv2
import os
import base64

from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url

from realesrgan.realesrgan import RealESRGANer

# RealESR-Gan configuration
netscale = 4
outscale = 4
dni_weight = None

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
realesr_gan_model_name = 'RealESRGAN_x4plus.pth'

def model_fn(model_dir):
    # loads SwinIR model
    realesr_gan_model_path = os.path.join(model_dir, realesr_gan_model_name)

    #loads RealESRGan Model
    realesr_gan_model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)

    real_esr_gan_upsampler = RealESRGANer(
        scale=netscale,
        model_path=realesr_gan_model_path,
        dni_weight=dni_weight,
        model=realesr_gan_model,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=True,
        gpu_id=0)

    print(f"===============loaded RealESRGanNer model====================")
    model = {}
    model['realesr_gan'] = real_esr_gan_upsampler
    return model

def input_fn(request_body, request_content_type):
    print("Received input request.")
    if "application/json" in request_content_type:
        data = json.loads(request_body)
        return data['image']
    raise ValueError("Unsupported content type: {}".format(request_content_type))

def predict_fn(input_data, model):
    print("Received predict request.")
    image_bytes = input_data.encode("ascii")
    nparr = np.frombuffer(base64.b64decode(image_bytes), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    data = ""

    try:
        print("Performing inference.")
        upsampler = model['realesr_gan'] 
        output, _ = upsampler.enhance(img, outscale=4)
        _, im_arr = cv2.imencode('.jpg', output)  # im_arr: image in Numpy one-dim array format.
        im_bytes = im_arr.tobytes()
        im_b64 = base64.b64encode(im_bytes)
        data = im_b64.decode('utf-8')
    except RuntimeError as error:
        print('Error', error)
        print('If you encounter CUDA out of memory, try to set --tile with a smaller number.')
    except Exception as error:
        print('Error', error)

    return data

def output_fn(prediction, content_type):
    return json.dumps({"generated_images": [prediction], "prompt":""}), content_type
