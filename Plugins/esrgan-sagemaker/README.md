# RealESRGAN upscaler Sagemaker endpoint

This package will deploy a sagemaker endpoint serving a model based on [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN]). This endpoint can then be used as an another upscaling method for the S3 upscaling workflow. 

## Deploy Sagemaker Endpoint

1. Create Sagemaker execution role. See [AWS Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html#sagemaker-roles-create-execution-role) on how to do this.

2. Download the model weights for the Real-ESRGAN model:

```
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth -P model/
```

3. Install SageMaker Python SDK and other dependencies

```
pip install -r requirements.txt
```

4. Modify the deployment script.

```
# Sagemaker execution role
role = "<ROLE ARN>"
```

5. Run the deployment script.

```
python deploy.py
sagemaker.config INFO - Not applying SDK defaults from location: /etc/xdg/sagemaker/config.yaml
sagemaker.config INFO - Not applying SDK defaults from location: /home/andklee/.config/sagemaker/config.yaml
------------!

Endpoint name: pytorch-inference-2024-05-10-21-13-39-305
```

6. Note the endpoint name created above for updating IAM roles to allow access and to point your clients to.

## Update IAM IRSA Role

1. You will need to update your IAM IRSA Role to allow the API to call the endpoint for upscaling.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "sagemaker:InvokeEndpoint"
            ],
            "Resource": [
                "arn:aws:s3:::<S3 bucket>/*",
                "arn:aws:sagemaker:<REGION>:<ACCT NUM>:endpoint/<Stable Diffusion Jumpstart endpoint name>",
                "arn:aws:sagemaker:<REGION>:<ACCT NUM>:endpoint/<Real-ESRGAN endpoint name>"
            ],
            "Effect": "Allow"
        }
    ]
}
```

## Update your clients

1. Ensure you update your clients to utilize the new endpoint name.

```
Testing/testBenchClient.py
...
endpoint = "<SAGEMAKER_ENDPOINT_NAME>"
...
```