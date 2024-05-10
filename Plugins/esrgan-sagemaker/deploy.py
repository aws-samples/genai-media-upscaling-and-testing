import boto3
from sagemaker.pytorch.model import PyTorchModel

session = boto3.session.Session()
region = session.region_name

# Sagemaker execution role
role = "arn:aws:iam::402484017262:role/service-role/AmazonSageMaker-ExecutionRole-20200828T151739"

pytorch_model = PyTorchModel(
                             model_data="model.tar.gz",
                             source_dir="./model/", 
                             role=role,
                             entry_point="inference.py",
                             image_uri=f"763104351884.dkr.ecr.{region}.amazonaws.com/pytorch-inference:2.0.0-gpu-py310-cu118-ubuntu20.04-sagemaker")

predictor = pytorch_model.deploy(instance_type='ml.g4dn.2xlarge', initial_instance_count=1)

print ("\n")
print(f"Endpoint name: {predictor.endpoint_name}")