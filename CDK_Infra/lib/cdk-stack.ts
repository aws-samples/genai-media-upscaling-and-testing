/**
   * File: cdk-stack.ts
   * Description: This file contains the CDK stack for the project. 
   * 
   * Author: @bainskb
   * Contributors: @bainskb
   * 
   * Date Created: 03/05/2024
   * Version: 1.0
   * 
   * References: N/A
   * 
   * Purpose:
   * This CDK stack will deploy the EKS Cluster and other relevant cloud resources for the Upscale
 * 
 */

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as eks from 'aws-cdk-lib/aws-eks';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import { NagSuppressions } from 'cdk-nag';
import { KubectlV29Layer } from '@aws-cdk/lambda-layer-kubectl-v29';
const request = require('sync-request');

export class CdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    //Creates SQS Queue for the video downscaler/upscaler containers
    const sqs_queue = new sqs.Queue(this, 'upscalerVideoQueue');
    
    //This will create the VPC for the EKS cluster
    //The VPC will have 2 public subnets and 4 private subnets split over 2 AZs
    //The private subnets will be used for the EKS cluster and the public subnets will be used for ELB.
    //The VPC will have a CIDR block of 10.0.0.0/16.
    const vpc = new ec2.Vpc(this, 'Vpc', {
      vpcName:'UpscaleVPC',
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      maxAzs: 2,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'PrivateSubnet1',
          subnetType:ec2.SubnetType.PRIVATE_WITH_EGRESS
        },
        {
          cidrMask: 24,
          name: 'PrivateSubnet2',
          subnetType:ec2.SubnetType.PRIVATE_WITH_EGRESS
        },
        {
          cidrMask: 24,
          name: 'PublicSubnet',
          subnetType:ec2.SubnetType.PUBLIC
        },
      ]
    });

    NagSuppressions.addResourceSuppressions(vpc, [
      { id: 'AwsSolutions-VPC7', reason: 'VPC is used for demo purposes only. Will not be used in Production.' },
    ]);

    // This role is built using the permissions from the Admin role ARN
    // Set 'mutable' to 'false' to use the role as-is and prevent adding new policies to it.
    const mastersRole = iam.Role.fromRoleArn(this, 'Role', 'arn:aws:iam::'+process.env.CDK_DEFAULT_ACCOUNT+':role/Admin', {
      mutable: false,
    });

    
    //This will create the EKS cluster with masters RBAC role using the private subnets
    const upscalerCluster = new eks.Cluster(this, 'upscaler', {      
      clusterName:'upscaler',
      version: eks.KubernetesVersion.V1_29,
      mastersRole: mastersRole,
      kubectlLayer: new KubectlV29Layer(this, 'kubectl'),
      defaultCapacity: 0,
      outputClusterName:true,
      outputMastersRoleArn:true,
      vpc: vpc,
      vpcSubnets: [{subnetGroupName:'PrivateSubnet1'},{subnetGroupName:'PrivateSubnet2'} ]
    });

    // create the namespace in the upscale K8 cluster
    const upscaleNamespace = upscalerCluster.addManifest('UpscaleNamespace', {
      apiVersion: 'v1',
      kind: 'Namespace',
      metadata: { name: 'upscale' },
    });

    //this will handle the IRSA role assignment to the cluster
    //Here we will configure the service account access
    const serviceAccount = upscalerCluster.addServiceAccount('IRSAServiceAccount', {
      name: 'iamserviceaccount',
      namespace: "upscale",
    });

    // the serviceAccount is going to be in the namespace and therefore it is dependant on the creation of the namespace
    serviceAccount.node.addDependency(upscaleNamespace)
    
    // add permissions to the service Account
    serviceAccount.addToPrincipalPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        //SageMaker permissions
        "sagemaker:InvokeEndpoint",
        //S3 permissions
        "s3:GetObject",
				"s3:PutObject",
        //SQS permissions
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
      ],
      resources: [
        sqs_queue.queueArn,
        //TO-DO:
        // "<SageMaker ARN>",
        //TO-DO:
        // "<S3 Bucket ARN>/*",
        //TO-DO:
        // "<SQS Queue ARN>"
      ]
    }));
    serviceAccount.addToPrincipalPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        //SQS permissions
        "sqs:ListQueues",
      ],
      resources: [
        "arn:aws:sqs:"+this.region+":"+this.account+":*",
      ]
    }));

    // If you are on an x86 Machine change the instance type. 
    const x86InstanceType = ec2.InstanceType.of(ec2.InstanceClass.M5, ec2.InstanceSize.XLARGE)  
    // const ARMInstanceType = ec2.InstanceType.of(ec2.InstanceClass.M7G, ec2.InstanceSize.XLARGE)
    //This will create the NodeGroup in the cluster
    const upscalerClusterNodeGroup = new eks.Nodegroup(this, 'upscalerClusterNodeGroup', {
      nodegroupName: "upscalerClusterNodeGroup",
      cluster: upscalerCluster,
      minSize: 4,
      maxSize: 4,
      instanceTypes: [
        x86InstanceType
      ]
    });

    // install AWS load balancer via Helm charts
    const awsLoadBalancerControllerVersion = 'v2.5.4';
    const awsControllerBaseResourceBaseUrl = `https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/${awsLoadBalancerControllerVersion}/docs`;
    const awsControllerPolicyUrl = `${awsControllerBaseResourceBaseUrl}/install/iam_policy.json`;
    // kube-system is default namespace of k8 and does not need to be installed
    const albNamespace = 'kube-system';

    const albServiceAccount = upscalerCluster.addServiceAccount('aws-load-balancer-controller', {
      name: 'aws-load-balancer-controller',
      namespace: albNamespace,
    });

    const policyJson = request('GET', awsControllerPolicyUrl).getBody();
    ((JSON.parse(policyJson)).Statement as []).forEach((statement, _idx, _array) => {
      albServiceAccount.addToPrincipalPolicy(iam.PolicyStatement.fromJson(statement));
    });

    const awsLoadBalancerControllerChart = upscalerCluster.addHelmChart('AWSLoadBalancerController', {
      chart: 'aws-load-balancer-controller',
      repository: 'https://aws.github.io/eks-charts',
      namespace: albNamespace,
      release: 'aws-load-balancer-controller',
      version: '1.5.5', // mapping to v2.5.4
      wait: true,
      timeout: cdk.Duration.minutes(15),
      values: {
        clusterName: upscalerCluster.clusterName,
        image: {
          repository: "public.ecr.aws/eks/aws-load-balancer-controller",
        },
        serviceAccount: {
          create: false,
          name: albServiceAccount.serviceAccountName,
        },
        // must disable waf features for aws-cn partition
        enableShield: false,
        enableWaf: false,
        enableWafv2: false,
      },
    });

    awsLoadBalancerControllerChart.node.addDependency(upscalerClusterNodeGroup);
    awsLoadBalancerControllerChart.node.addDependency(albServiceAccount);
    awsLoadBalancerControllerChart.node.addDependency(upscalerCluster.openIdConnectProvider);
    awsLoadBalancerControllerChart.node.addDependency(upscalerCluster.awsAuth);

    const certManagerNamespace = "cert-manager";

    const certManagerChart = upscalerCluster.addHelmChart('CertManagerChart', {
      chart: 'cert-manager',
      repository: 'https://charts.jetstack.io',
      namespace: certManagerNamespace,
      release: 'cert-manager',
      version: 'v1.12.0',
      wait: true,
      timeout: cdk.Duration.minutes(15),
      values: {
        "installCRDs": true
      }
    });

    const upscalerAPIRepository = new ecr.Repository(this, 'upscalerAPIRepository', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      repositoryName: "upscaler-api"
    });
    new cdk.CfnOutput(this, 'APIECRRepoURI', { value: upscalerAPIRepository.repositoryUri });

    const videoUpscalerAPIRepository = new ecr.Repository(this, 'videoUpscalerAPIRepository', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      repositoryName: "upscaler-video"
    });

    new cdk.CfnOutput(this, 'VIDEOECRRepoURI', { value: videoUpscalerAPIRepository.repositoryUri });
  }
}
