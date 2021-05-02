import os
import pandas as pd
import glob
import cv2
import numpy as np
import matplotlib.pyplot as plt
from preprocess import preprocess
import torch
import h5py
import tkinter as tk
from tkinter import filedialog


# Check GPU availability
print("Available GPU", torch.cuda.get_device_name(0))

# Set data directories
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = WORKING_DIR + "/maps"
DATA_CSV = "training_data.csv"
DATA_IMG = "img"
HDF5_DIR = WORKING_DIR + "/hdf5"
CAMERA_LIST = ["center", "right", "left"]
BATCH_SIZE = 2500


def data_to_hdf5():
    """
    Reads data (images and labels) from WORKING_DIR/maps/ and saves it to hdf5 files of size BATCH_SIZE each
    Args:
        None
    Returns:
        None
    """

    print("[info] Creaing new hdf5 files from map data...\n")

    print("Please make sure your data structure is as \n{}/maps/Map1/data[0,1,2...]/img".format(WORKING_DIR))
    if not os.path.exists(HDF5_DIR):
        os.makedirs(HDF5_DIR)

    # Get all maps
    all_maps = glob.glob(DATA_DIR + "/*")

    if not all_maps:
        print("Maps not found")
        exit(0)
    elif "Map1" not in all_maps[0]:
        print("Incorrect directory structure")
        exit(0)

    maps_data = []
    maps_data += [glob.glob(map + "/*") for map in all_maps]

    images = []
    labels = []
    correction = [0.0, -0.02, 0.02]     # corrections w.r.t. [center right left]

    # Sample test
    sample_img_path = glob.glob(DATA_DIR + "/**/*.jpg", recursive=True)[0]
    img = cv2.imread(sample_img_path)
    plt.imshow(preprocess(img), cmap="gray")
    plt.show()

    batch = 0 
    batch_idx = 0

    for data in maps_data[0]:                               # Iterate over each map
        csv_df = pd.read_csv(data + "/" + DATA_CSV, header=None)

        for index, row in csv_df.iterrows():                # Iterate over data for each map
            # First column of DATA_CSV contains image timestamp
            img_time = row[0]
            # Second column of DATA_CSV contains steering value
            steer = row[1]

            for i in range(3):                              # Reading all CAMERA_LIST images
                img_path = data + "/" + DATA_IMG + "/" + \
                    CAMERA_LIST[i] + "-" + img_time + ".jpg"
                img = cv2.imread(img_path)
                img_processed = preprocess(img)

                images.append(img_processed)
                labels.append(float(steer) + correction[i])

                images.append(np.fliplr(img_processed))
                labels.append(-(float(steer) + correction[i]))

                batch += 1

                if batch % BATCH_SIZE == 0:
                    h5_filename = os.path.join(HDF5_DIR, "batch-{}.h5".format(batch_idx))
                    with h5py.File(h5_filename, 'w') as hfile:
                        hfile.create_dataset('images', data=images)
                        hfile.create_dataset('labels', data=labels)

                        print("Batch {} saved".format(batch_idx))
                        images = []
                        labels = []
                        batch_idx += 1
    
    # Save the remaining data 
    h5_filename = os.path.join(HDF5_DIR, "batch-{}.h5".format(batch_idx))
    with h5py.File(h5_filename, 'w') as hfile:
        hfile.create_dataset('images', data=images)
        hfile.create_dataset('labels', data=labels)

        print("Batch {} saved".format(batch_idx))
        images = []
        labels = []
        batch_idx += 1


def data_from_hdf5():
    print("[info] Loading data from saved hdf5...")
    for i, hf_name in enumerate(glob.glob(HDF5_DIR + "/*")):
        print(hf_name)
        # h5_filename = os.path.join(HDF5_DIR, "batch-{}.h5".format(i))
        with h5py.File(hf_name, 'r') as hfile:
            n1 = np.array(hfile.get('images'))
            n2 = np.array(hfile.get('labels'))
            print(n1.shape)
            print(n2.shape)


def dir_selector():
    root = tk.Tk()
    root.withdraw()

    DATA_DIR = filedialog.askdirectory(parent=root,initialdir="/",title='Please select your maps directory')
    print("DATA_DIR changed to", DATA_DIR)

try:
    user_input = input("Press [c] to Create new HDF5 from data or \nPress [e] to Load from existing HDF5\n Your Selection (press enter): ")
    if 'c' in user_input:
        data_to_hdf5()
    elif 'e' in user_input:
        data_from_hdf5()
except KeyboardInterrupt:
    print("\n[info] Aborted by User")