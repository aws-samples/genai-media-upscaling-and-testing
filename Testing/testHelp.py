"""
File: testHelp.py
Description: This is a helper program that will generate a csv file for 
every .jpg, jpeg, or png in a directory. The csv file will contain the entire path of the image file.

Author: @bainskb
Contributors: @bainskb

Date Created: 03/05/2024
Version: 1.0

References: N/A

Purpose:
    This will be used to generate a CSV to be used by the testBenchClient.
"""

import os
import csv


def main():
    # get the directory name
    directory = input("Enter a directory name: ")

    # if the directory exists, continue
    if os.path.exists(directory):
        # create a file object for the output file
        output_file = open("testFile.csv", "w", newline="")

        # create a csv writer object
        writer = csv.writer(output_file)

        # write the header row, Path,  to output_file
        writer.writerow(["image_path"])


        # if there are subdirectories, check for .jpg, .jpeg, or .png files in each subdirectory
        for subdir, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                    # write the path of the file to the output file, with a newline character at the end
                    filepath = os.path.join(subdir, file)
                    writer.writerow([filepath])

        # close the file
        output_file.close()
        print("File saved.")
    else:
        print("Directory does not exist.")


if __name__ == "__main__":
    main()