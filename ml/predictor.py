# TODO: convert this to a seperate class

from datetime import timedelta
from configuration import get_controller_timeperiod
from configuration import get_ml_windowsize
import numpy as np

original_data = []
predicted_data = []
window_size = get_ml_windowsize()

def add_data(reply_data):
    data_point = reply_data
    original_data.append({"timestamp" : data_point['timestamp'], 
                        "num_flows" : data_point['num_flows'], 
                        "pkt_cnt" : data_point['pkt_cnt'], 
                        "pkt_len" : data_point['pkt_len']})

    if(len(original_data) > window_size):
        original_data.pop(0)

def predict():
    apc = [x['pkt_cnt'] for x in original_data]
    latest_timestamp = original_data[-1]["timestamp"]
    pred_value = float(sum(apc)) / len(apc) # currently taking just mean
    predicted_data.append({"timestamp" : latest_timestamp + timedelta(seconds=get_controller_timeperiod()), 
                            "predicted_pkt_cnt" : pred_value})
    if(len(predicted_data) > window_size):
        predicted_data.pop(0)
    return pred_value

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