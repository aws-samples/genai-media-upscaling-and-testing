"""
File: FlaskAPI.py
Description: This file contains the Flask API for the upscale_s3 project.

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    This API will be deployed as a Docker Container to ECR and then implemented into the EKS Cluster 
"""
from flask import Flask, request, jsonify
from downscale_s3 import disect_request_store, disect_request_retrieve, disect_request_store_video, disect_request_retrieve_video, disect_request_get_video_status
import os
app = Flask(__name__)  

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}, 200)

@app.route('/store', methods=['POST'])
def store_image():
    try: 
        status = disect_request_store(request)
        data = status["data"]
        statusCode = status["code"]
        if statusCode == 200:
            return jsonify({'data': data}, 200)
        else:
            return jsonify({'error': 'Unable to store image: ' + str(status)}, 500)
    except Exception as e:
        status = ("Unable to store" + str(e))
        return jsonify({'error': 'Unable dissect request: ' + str(status)}, 500)

@app.route('/storeVideo', methods=['POST'])
def store_video():
    try: 
        status = disect_request_store_video(request)
        data = status["data"]
        statusCode = status["code"]
        if statusCode == 200:
            return jsonify({'data': data}, 200)
        else:
            return jsonify({'error': 'Unable to store video: ' + str(status)}, 500)
    except Exception as e:
        status = ("Unable to store" + str(e))
        return jsonify({'error': 'Unable dissect request: ' + str(status)}, 500)
    

@app.route('/retrieve', methods=['GET'])
def retrieve_image():
    try:
        status = disect_request_retrieve(request)
        statusCode = status['code']
        data = status['data']
        if statusCode == 200:
            return jsonify({'data': data}, 200)
        else:
            return jsonify({'error': 'Unable to retrieve image: ' + str(data)}, 500)
    except Exception as e:
        print("Unable to retrieve" + str(e))
        return jsonify({'error': 'Unable dissect request'}, 500)
    
@app.route('/retrieveVideo', methods=['GET'])
def retrieve_video():
    try:
        status = disect_request_retrieve_video(request)
        statusCode = status['code']
        data = status['data']
        if statusCode == 200:
            return jsonify({'data': data}, 200)
        else:
            return jsonify({'error': 'Unable to retrieve video: ' + str(data)}, 500)
    except Exception as e:
        print("Unable to retrieve" + str(e))
        return jsonify({'error': 'Unable dissect request'}, 500)
    
@app.route('/getVideoStatus', methods=['GET'])
def get_video_status():
    try:
        status = disect_request_get_video_status(request)
        statusCode = status['code']
        data = status['data']
        if statusCode == 200:
            return jsonify({'data': data}, 200)
        else:
            return jsonify({'error': 'Unable to retrieve video status: ' + str(data)}, 500)
    except Exception as e:
        print("Unable to get video status" + str(e))
        return jsonify({'error': 'Unable dissect request'}, 500)

if __name__ == '__main__':
    cert_path = os.getenv('SSL_CERT')
    key_path = os.getenv('SSL_KEY')
    
    if cert_path is not None and key_path is not None:
        print("secure")
        context = (cert_path, key_path)
        # serve(app, host='0.0.0.0', port=5000, ssl_context=context)
        app.run(debug=False, ssl_context=context, host='0.0.0.0', port=5000)
    else:
        print("unsecure")
        # serve(app, host='0.0.0.0', port=5000)
        app.run(debug=False, host='0.0.0.0', port=5000)