"""
File: testBenchClient.py
Description: This is test bench client. It will call the API to run tests. 

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References:
Bhattiprolu, S. (2023). python_for_microscopists. GitHub.
* https://github.com/bnsreenu/python_for_microscopists/blob/master/191_measure_img_similarity.py 

Purpose:
    This file is used to test the API and send images and retrieve images to the API.
"""
import datetime
import requests
import base64
import os
import csv
import cv2
import warnings
# Suppress all warnings
warnings.filterwarnings("ignore")
# TestBench Inputs
# Make sure your inputs  match the deployment you are testing against
s3_bucket = "<S3_BUCKET_NAME>"
endpoint = "<SAGEMAKER_ENDPOINT_NAME>"
ELB_DNS = "k8s-upscale-upscale-<ELB_ID>.elb.<REGION>.amazonaws.com"
HTTPS = "https://"
API_URL = HTTPS + ELB_DNS
# Local Test API
# API_URL = "http://127.0.0.1:5000"

# Based on work from Sreenivas Bhattiprolu
def orb_sim(img1, img2):
  # SIFT is no longer available in cv2 so using ORB
  orb = cv2.ORB_create()

  # detect key points and descriptors
  kp_a, desc_a = orb.detectAndCompute(img1, None)
  kp_b, desc_b = orb.detectAndCompute(img2, None)

  # define the brute force matcher object
  bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
  #perform matches. 
  matches = bf.match(desc_a, desc_b)
  #Look for similar regions with distance < 50. Goes from 0 to 100 so pick a number between.
  similar_regions = [i for i in matches if i.distance < 50]  
  if len(matches) == 0:
    return 0
  return len(similar_regions) / len(matches)


def send_image_to_api(image_path, api_url, s3Key):
    try: 
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
    except FileNotFoundError:
        print(f"File {image_path} not found.")
        return
        
    
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    data = {'image': encoded_image, "s3_bucket":s3_bucket, "s3_key_name": s3Key, "endpoint":endpoint, 'upscaleMethod': "stableDiffusionJT"}

    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url+'/store', headers=headers, json=data, verify=False)
    return response.json()

# will send the s3_key as an query parameter argument
def retrieve_image_from_api(api_url, s3_key):
    url = f"{api_url}/retrieve?s3_key={s3_key}&s3_bucket={s3_bucket}&endpoint={endpoint}"
    response = requests.get(url, verify=False)
    return response.json()
    
def call_api(image_src_path, image_dest_path):
    # Examples
    # image_path = '../Resources/SampleImages/wolf.jpg'
    # s3_key = "wolf.jpg"
    image_path = image_src_path
    # grab the file name from the path
    s3_key = image_path.split('/')[-1]
    print("This is the s3_key", s3_key)
    print("This is the image path:", image_path)
    api_url = API_URL

    # send the image to the api
    try:    
        send_response = send_image_to_api(image_path, api_url, s3_key)
    except Exception as e:
        print("Failed to send with: ", e)
        print(send_response)
        return "Error Send"
    
    print("Successfully sent image:")
    print(send_response)

    try:
        retrieve_response = retrieve_image_from_api(api_url, s3_key)
    except Exception as e:
        print("Failed to retrieve with: ", e)
        return "Error Retrieve"
    
    if retrieve_response[1] == 200:
        print("Received response:")
        image_data = retrieve_response[0]['data']
        if(image_data == "Unable to upscale image" or image_data == "upscale failed"):
            print(retrieve_response)
            return "Error Upscale"
        image_data = base64.b64decode(image_data)
        with open(image_dest_path, 'wb') as f:
            f.write(image_data)
        return "Success"
    else:
        print(retrieve_response[0]['error'])
        return "Error Response Retrieve"

def run_tests_from_arrs(arr_of_paths, destPaths):
    print("Running Similarity tests")
    # make sure that the number of paths is equal to the number of destPaths
    if len(arr_of_paths) != len(destPaths):
        print("Number of paths and destPaths do not match")
        return "Error"
    try:
        testResults = []
        for i in range(len(arr_of_paths)):
            # Make sure image exists at the dest path before opening
            if not os.path.exists(destPaths[i]):
                # print("destPath does not exist")
                testResults.append("NaN")
                continue
            else:
                img1 = cv2.imread(arr_of_paths[i], 0)
                img2 = cv2.imread(destPaths[i], 0)
            # if either of the images are NoneType then we will append "NaN" to the testResults array.
            if img1 is None or img2 is None:
                print("Cannot read image")
                testResults.append("NaN")
            else:
                # with both images loaded we will make img1 the same dimension as img2 before running test. 
                img1 = cv2.resize(img1, (img2.shape[1], img2.shape[0]))
                orb_similarity = orb_sim(img1, img2)
                # orb_similarity is a float between 0 and 1, so we will convert it to a single or double digit percentage string and add it to the testResults array. 
                #  for example if orb_similarity is 0.5, then orb_score will be "50%" if orb_similarity is 0.09 then the orb_score will be 9%. if the orb_similarity is 0.009 then the score is
                float_percentage = orb_similarity * 100
                orb_score = int(float_percentage)
                orb_score_string = str(orb_score) + "%"
                testResults.append(orb_score_string)
        if "NaN" in testResults:
            print("All test NOT passed; at least one of the images is NoneType")
        else: 
            print("All tests passed")
        return testResults
    except Exception as e:
        print("Error:", e)
        return "Error"
    
def create_csv_file(paths, destPaths, test_results, curr_results_folder):
    # here we create a new csv file in the current results folder
    # it will have 3 columns: path, destPath, testResults
    print("Creating results CSV file")
    try:
        csv_file = os.path.join(curr_results_folder, "testResults.csv")
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['path', 'destPath', 'testResults'])
            for i in range(len(paths)):
                writer.writerow([paths[i], destPaths[i], test_results[i]])
        return "Success"
    except Exception as e:
        print("Error:", e)
        return "Error"

def run_tests_from_csv_file(arr_of_paths, curr_results_folder):
    print("Running tests from CSV file:")
    print("-------------------------------------------------")
    try: 
        paths = []
        destPaths = []
        for path in arr_of_paths:
            # create the image name from the path
            image_name = path.split('/')[-1]
            # create the image destination path
            image_dest_path = os.path.join(curr_results_folder, image_name)
            paths.append(path)
            destPaths.append(image_dest_path)
            # call the api
            api_result = call_api(path, image_dest_path)
            if api_result == "Success":
                print(f"Image {image_name} saved to {image_dest_path}")
            else:
                # print(f"Error saving image {image_name} to {image_dest_path}")
                print("Error: ", api_result)
            
            print("-------------------------------------------------")
        
        print("Test results saved to", curr_results_folder)
        # print("here is the paths array we are going to use:", paths)
        # print("here is the destPaths array we are going to use:", destPaths)
        test_results = run_tests_from_arrs(paths, destPaths)
        # with the src paths in paths, the dest paths in destPaths, and the test results in test_results, we can write the results to a csv file
        print("Here are the similarity scores:", test_results)

        status = create_csv_file(paths, destPaths, test_results, curr_results_folder)
        return status
    except Exception as e:
        print("Error:", e)
        return "Error"

def validate_csv_file(csv_file):
    if not os.path.exists(csv_file):
        raise FileNotFoundError("Path does not exists")
    
    if not csv_file.endswith('.csv'):
        raise ValueError("File must be a csv file")
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        if len(headers) != 1:
            raise ValueError("CSV file should have one column")
        
        for row in reader:
            if len(row) != 1:
                raise ValueError("Each row should have one image path")
            if not os.path.exists(row[0]):
                raise FileNotFoundError("Image path does not exist")
    
    print("All validations tests passed!")
    return True
        
def read_csv_file(csv_file):
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        arr_of_paths = []
        for row in reader:
            arr_of_paths.append(row[0])
        return arr_of_paths


def main(csv_file):
    good = validate_csv_file(csv_file)
    if good:
        fileName = csv_file.split('/')[-1]
        print("This is the CSV file: ", fileName)
        arr_of_paths = read_csv_file(csv_file)
    else:
        print("This is not a csv file")

    # file is good and we can use the array of paths to send the images to the api, and then test
    # we want to store the results images into a folder labeled resultsTime: followed by a timestamp when the results were made
    
    # create the results folder if it does not exist
    results_folder = "TestResults"
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
        print("TestResults folder created")
        
    # get the timestamp for this run of the test bench
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    curr_results_folder = os.path.join(results_folder, timestamp)
    os.makedirs(curr_results_folder)
    # now we can send the images to the api and store the results in the results folder
    try:
        run_tests_from_csv_file(arr_of_paths, curr_results_folder)  
    except Exception as e:
        print("An error occurred:", e)
        raise e
    print("TestBench complete. Navigate to TestResults to see detailed report")

if __name__ == '__main__':
    # to run this test bench you will provide a csv file. this csv file will have a list of image paths
    csv_file = input("Enter the CSV file path: ")
    main(csv_file)