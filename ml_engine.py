import joblib
import numpy as np
import pandas as pd

class TrainedModelEngine:
    def __init__(self, model_path='model/fault_detection_model.pkl'):
        """Loads the serialized dictionary and extracts the inner model object."""
        loaded_dict = joblib.load(model_path)
        
        self.model = loaded_dict['model']
        
    def predict_live_data(self, curr_vib, curr_temp, curr_press, vib_history, temp_history):
        """
        Engineers moving time-series features in real-time and executes inference 
        against the exact feature schema expected by the trained model.
        """
    
        recent_vib = vib_history[-10:] if len(vib_history) >= 10 else [curr_vib]
        recent_temp = temp_history[-10:] if len(temp_history) >= 10 else [curr_temp]
        
        
        mean_temp = np.mean(recent_temp)
        
        
        rms_vibration = np.sqrt(np.mean(np.square(recent_vib)))
        
        
        input_df = pd.DataFrame([{
            'Vibration (mm/s)': curr_vib,
            'Temperature (°C)': curr_temp,
            'Pressure (bar)': curr_press,
            'RMS Vibration': rms_vibration,
            'Mean Temp': mean_temp
        }])
        
        
        prediction = self.model.predict(input_df)
        return int(prediction[0])