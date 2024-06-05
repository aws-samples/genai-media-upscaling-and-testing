# RealESRGAN upscaler Sagemaker endpoint

This package will deploy a sagemaker endpoint serving a model based on [Swin2SR](https://github.com/mv-lab/swin2sr]). This endpoint can then be used as an another upscaling method for the S3 upscaling workflow. 

## Prerequisites

* Python 3.11 (**Note** Python 3.12 will not work as there is a [known issue](https://github.com/aws/sagemaker-python-sdk/issues/4534) in the sagemaker python sdk that the deployment script depends on. It is recommended to use an venv with Python 3.11.)

## Deploy Sagemaker Endpoint

1. Create Sagemaker execution role. See [AWS Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html#sagemaker-roles-create-execution-role) on how to do this.

2. Download the model weights for the Real-ESRGAN model and create the model.tar.gz:

```
wget https://github.com/mv-lab/swin2sr/releases/download/v0.0.1/Swin2SR_RealworldSR_X4_64_BSRGAN_PSNR.pth
tar -czf model.tar.gz Swin2SR_RealworldSR_X4_64_BSRGAN_PSNR.pth
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
                "arn:aws:sagemaker:<REGION>:<ACCT NUM>:endpoint/<Swin2SR endpoint name>"
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