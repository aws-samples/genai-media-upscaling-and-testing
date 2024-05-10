ARG AWS_REGION=us-east-1
FROM 763104351884.dkr.ecr.${AWS_REGION}.amazonaws.com/pytorch-inference:2.0.0-gpu-py310-cu118-ubuntu20.04-sagemaker
WORKDIR /workdir
COPY RealESRGAN_x4plus.pth /opt/ml/model/
COPY code/ /opt/ml/model/code/
EXPOSE 8080
ENTRYPOINT [ "python", "/usr/local/bin/dockerd-entrypoint.py" ]
