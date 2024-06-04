import torch
import torch.nn as nn
import json
from pathlib import Path
import numpy as np
import cv2
import os
import base64

from swinir.load_model import define_model

# SwinIR configuration
scale_factor = 4
window_size = 8

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
swinir_model_name = 'Swin2SR_RealworldSR_X4_64_BSRGAN_PSNR.pth'

def model_fn(model_dir):
    # loads SwinIR model
    swinir_model_path = os.path.join(model_dir, swinir_model_name)
    print(f"========model path: {swinir_model_path} ======")

    #loads RealESRGan Model
    swinir_model = define_model(swinir_model_path, "real_sr", scale_factor)
    
    swinir_model = swinir_model.to(device)
    swinir_model.eval()
    return swinir_model

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
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR).astype(np.float32) / 255.
    img = np.transpose(img if img.shape[2] == 1 else img[:, :, [2, 1, 0]], (2, 0, 1))  # HCW-BGR to CHW-RGB
    img = torch.from_numpy(img).float().unsqueeze(0).to(device)  # CHW-RGB to NCHW-RGB
    data = ""

    try:
        print("Performing inference.")
        with torch.no_grad():
            # pad input image to be a multiple of window_size
            _, _, h_old, w_old = img.size()
            h_pad = (h_old // window_size + 1) * window_size - h_old
            w_pad = (w_old // window_size + 1) * window_size - w_old
            img = torch.cat([img, torch.flip(img, [2])], 2)[:, :, :h_old + h_pad, :]
            img = torch.cat([img, torch.flip(img, [3])], 3)[:, :, :, :w_old + w_pad]
            print(f"==========================image input size: {img.shape} ======================")
            output = model(img)
            output = output[..., :h_old * scale_factor, :w_old * scale_factor]

            output = output.data.squeeze().float().cpu().clamp_(0, 1).numpy()
            if output.ndim == 3:
                output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))  # CHW-RGB to HCW-BGR
            output = (output * 255.0).round().astype(np.uint8)  # float32 to uint8
            _, im_arr = cv2.imencode('.jpg', output)  # im_arr: image in Numpy one-dim array format.
            im_bytes = im_arr.tobytes()
            im_b64 = base64.b64encode(im_bytes)
            data = im_b64.decode('utf-8')
            torch.cuda.empty_cache()
            print(f'torch cache cleared')
    except RuntimeError as error:
        print('Error', error)
        print('If you encounter CUDA out of memory, try to set --tile with a smaller number.')
    except Exception as error:
        print('Error', error)

    return data

def output_fn(prediction, content_type):
    return json.dumps({"generated_images": [prediction], "prompt":""}), content_type
