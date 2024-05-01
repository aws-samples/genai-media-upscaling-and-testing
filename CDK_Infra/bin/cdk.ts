#!/usr/bin/env node
/**
   * File: cdk.ts
   * Description: This file contains the configuration for the CDK stack for the project. 
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
   * This gets the stack contents from lib and creates an instance of it in the proper environment. 
 * 
 */
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CdkStack } from '../lib/cdk-stack';

const app = new cdk.App();
new CdkStack(app, 'K8Stackv29', {
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});