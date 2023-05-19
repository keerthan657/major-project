# TODO: convert this to a seperate class

from datetime import timedelta
from configuration import get_controller_timeperiod
from configuration import get_ml_windowsize, get_dl_model, get_controller_timeperiod
import numpy as np
import statistics
import pickle

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from nbeats_pytorch.model import NBeatsNet

class VAE(nn.Module):
    def __init__(self, input_size, latent_size):
        super(VAE, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
        )
        self.latent_mean = nn.Linear(32, latent_size)
        self.latent_logvar = nn.Linear(32, latent_size)
        self.decoder = nn.Sequential(
            nn.Linear(latent_size, 32),
            nn.ReLU(),
            nn.Linear(32, input_size),
            nn.Sigmoid(),
        )

    def encode(self, x):
        hidden = self.encoder(x)
        mean = self.latent_mean(hidden)
        logvar = self.latent_logvar(hidden)
        return mean, logvar

    def reparameterize(self, mean, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mean + eps * std
        return z

    def decode(self, z):
        return self.decoder(z)

    def forward(self, x):
        mean, logvar = self.encode(x)
        z = self.reparameterize(mean, logvar)
        x_recon = self.decode(z)
        return x_recon, mean, logvar

# Min-Max normalization
def normalize(data, min1, max1):
    data = np.array(data)
    normalized_data = (data - min1) / (max1 - min1)
    return normalized_data

def calculate_statistics(numbers):
    mean = statistics.mean(numbers)
    std_dev = statistics.stdev(numbers)
    minimum = min(numbers)
    maximum = max(numbers)
    count = len(numbers)
    print("Mean:", mean)
    print("Standard Deviation:", std_dev)
    print("Minimum:", minimum)
    print("Maximum:", maximum)
    print("Count:", count)

original_data = []
predicted_data = []
window_size = get_ml_windowsize()
dl_model = get_dl_model()

def add_data(reply_data):
    data_point = reply_data
    original_data.append({"timestamp" : data_point['timestamp'], 
                        "num_flows" : data_point['num_flows'], 
                        "pkt_cnt" : data_point['pkt_cnt'], 
                        "pkt_len" : data_point['pkt_len']})

    if(len(original_data) > window_size):
        original_data.pop(0)
    
    return original_data

# TODO: start from here
def predict(window):
    if dl_model=='RBM':
        return predict_RBM(window)
    elif dl_model=='VAE':
        return predict_VAE(window)
    elif dl_model=='NBEATS':
        return predict_NBEATS(window)
    else:
        return predict_MEAN(window)

def predict_RBM(window):
    
    # load model save file
    with open('rbm_model.pkl', 'rb') as file:
        rbm = pickle.load(file)

    # if not enough points, wait
    if(len(window) < window_size):
        return -1

    # add timestamp data to the window variable
    window1 = []
    for i in range(window_size):
        window1.append(i/10)
        window1.append(window[i]['pkt_cnt']) # TODO: normalize this & fix normalization values same for all models
    
    # get anomaly score (for window size of 10)
    score = rbm.score_samples([window1])

    return score

def predict_VAE(window):
    
    # load model save file
    # Create an instance of the VAE model
    input_size = window_size * 2
    latent_size = 2
    model = VAE(input_size, latent_size)

    # Load the saved VAE model from a file
    model.load_state_dict(torch.load('vae_model.pth'))

    # Set the VAE model to evaluation mode
    model.eval()

    # if not enough points, wait
    if(len(window) < window_size):
        return -1

    # add timestamp data to window variable
    window1 = []
    for i in range(window_size):
        window1.append(i/10)
        window1.append(normalize(window[i]['pkt_cnt'], 1255, 1926))
    print('window1: ', window1)

    # get anomaly score (MSE, for window size of 10)
    with torch.no_grad():
        window2 = [window1]
        window2 = torch.tensor(window2, dtype=torch.float32)
        print('window2: ', window2)
        window2 = window2.reshape(1, -1)
        recon_window, mean, logvar = model(window2)
        mse = torch.mean(torch.pow(window2 - recon_window, 2))

    return mse

def predict_NBEATS(window):
    
    # load model save file
    model_pytorch = NBeatsNet.load('nbeats_model.th')

    # if not enough points, wait
    if(len(window) < window_size):
        return -1

    # add timestamp data to window variable
    window1 = []
    for i in range(window_size):
        window1.append(i/10)
        window1.append(normalize(window[i]['pkt_cnt'], 1255, 1926))
    print('window1: ', window1)

    # get prediction
    pred_val = model_pytorch.predict(np.array(window1))
    pred_val = pred_val[0][0]
    print('predicted: ', pred_val)

    # store prediction, to further calculate anomaly score (MSE, for window size of 10)
    predicted_data.append({
        "timestamp" : window[-1]['timestamp'] + timedelta(seconds=get_controller_timeperiod()),
        "pkt_cnt" : pred_val
    })

    # print('window: ', window)
    # print('predicted: ', predicted_data)

    # apply windowing to predicted_data list also
    if(len(predicted_data) < window_size):
        return -1

    # Extract timestamps from each list
    timestamps1 = [d['timestamp'].replace(microsecond=0) for d in window]
    timestamps2 = [d['timestamp'].replace(microsecond=0) for d in predicted_data]

    # Find common timestamps
    common_timestamps = set(timestamps1).intersection(timestamps2)

    # if not enough common values, return
    if(len(common_timestamps) < 2):
        return -2

    # Filter out dictionaries with common timestamps
    common_data_list1 = [d for d in window if d['timestamp'].replace(microsecond=0) in common_timestamps]
    common_data_list2 = [d for d in predicted_data if d['timestamp'].replace(microsecond=0) in common_timestamps]

    # Calculate MSE for the 'val' of common timestamps
    d1 = window
    d2 = predicted_data
    mse = np.mean([(normalize(d1['pkt_cnt'], 1255, 1926) - d2['pkt_cnt']) ** 2 for d1, d2 in zip(common_data_list1, common_data_list2)])

    return mse

def predict_MEAN(window):
    pass

def z_thresholding(original_timestamps, predicted_timestamps, original_values, predicted_values):
    # Find common timestamps
    common_timestamps = set(original_timestamps) & set(predicted_timestamps)

    # Filter out original and predicted values for common timestamps
    common_original_values = [x for x, timestamp in zip(original_values, original_timestamps) if timestamp in common_timestamps]
    common_predicted_values = [x for x, timestamp in zip(predicted_values, predicted_timestamps) if timestamp in common_timestamps]

    # Find the errors & squared errors
    errors = np.array(common_original_values) - np.array(common_predicted_values)
    squared_errors = errors**2

    # Calculate mean and standard deviation
    if len(squared_errors)==0:
        return []
    mean = np.mean(squared_errors)
    std = np.std(squared_errors)

    # Fix Z value
    z = 1

    # Calculate threshold and anomalies
    threshold = mean + (z * std)
    anomalies = (squared_errors > threshold)

    # Give anomaly data to controller, to plot
    anomalies_data = []
    for i in range(len(common_timestamps)):
        if anomalies[i]==1:
            anomalies_data[i] = {"timestamp" : common_timestamps[i], "anomaly" : True}
        else:
            anomalies_data[i] = {"timestamp" : common_timestamps[i], "anomaly" : False}
    return anomalies_data

    # # Calculate the number of anomalies
    # num_anomalies = np.sum(squared_errors > threshold)

    # # Adjust Z value based on the number of anomalies
    # # Vary Z value to increase/decrease based on number of anomalies found
    # # TODO: properly adjust these values
    # if num_anomalies > 10:
    #     z += 1
    # elif num_anomalies < 5:
    #     z -= 1