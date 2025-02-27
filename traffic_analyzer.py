import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import pandas as pd
import matplotlib.pyplot as plt
import datetime

class VehicleDetector:
    def __init__(self, model_path):
        self.net = cv2.dnn.readNet(model_path)
        self.classes = []
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        
    def detect(self, frame):
        height, width, channels = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        
        class_ids = []
        confidences = []
        boxes = []
        
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5 and class_id in [2, 5, 7]:  # car, bus, truck
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        return boxes, class_ids, indexes

class TrafficAnalyzer:
    def __init__(self):
        self.vehicle_detector = VehicleDetector("yolov3.weights")
        self.traffic_data = pd.DataFrame(columns=['timestamp', 'vehicle_count', 'density', 'flow_rate'])
        
    def analyze_frame(self, frame, timestamp):
        boxes, class_ids, indexes = self.vehicle_detector.detect(frame)
        
        # Calculate metrics
        vehicle_count = len(indexes)
        
        # Basic density calculation (vehicles per area)
        frame_area = frame.shape[0] * frame.shape[1]
        density = vehicle_count / frame_area if frame_area > 0 else 0
        
        # Store data
        self.traffic_data = self.traffic_data.append({
            'timestamp': timestamp,
            'vehicle_count': vehicle_count,
            'density': density,
            'flow_rate': 0  # Will be calculated based on time series
        }, ignore_index=True)
        
        # Draw bounding boxes
        result_frame = frame.copy()
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(self.vehicle_detector.classes[class_ids[i]])
                cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(result_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return result_frame, vehicle_count, density
    
    def calculate_flow_rate(self, time_window=5):
        """Calculate flow rate over a sliding window of minutes"""
        if len(self.traffic_data) < 2:
            return
        
        # Convert timestamp to datetime if it's string
        if isinstance(self.traffic_data['timestamp'][0], str):
            self.traffic_data['timestamp'] = pd.to_datetime(self.traffic_data['timestamp'])
        
        for i in range(len(self.traffic_data)):
            start_time = self.traffic_data.iloc[i]['timestamp'] - pd.Timedelta(minutes=time_window)
            window_data = self.traffic_data[(self.traffic_data['timestamp'] > start_time) & 
                                           (self.traffic_data['timestamp'] <= self.traffic_data.iloc[i]['timestamp'])]
            
            if len(window_data) > 1:
                time_diff = (window_data['timestamp'].max() - window_data['timestamp'].min()).total_seconds() / 60
                if time_diff > 0:
                    self.traffic_data.loc[i, 'flow_rate'] = window_data['vehicle_count'].mean() / time_diff
    
    def visualize_data(self):
        """Visualize the collected traffic data"""
        plt.figure(figsize=(15, 10))
        
        # Plot vehicle count over time
        plt.subplot(3, 1, 1)
        plt.plot(self.traffic_data['timestamp'], self.traffic_data['vehicle_count'])
        plt.title('Vehicle Count Over Time')
        plt.xlabel('Time')
        plt.ylabel('Count')
        
        # Plot density over time
        plt.subplot(3, 1, 2)
        plt.plot(self.traffic_data['timestamp'], self.traffic_data['density'])
        plt.title('Traffic Density Over Time')
        plt.xlabel('Time')
        plt.ylabel('Density')
        
        # Plot flow rate over time
        plt.subplot(3, 1, 3)
        plt.plot(self.traffic_data['timestamp'], self.traffic_data['flow_rate'])
        plt.title('Traffic Flow Rate Over Time')
        plt.xlabel('Time')
        plt.ylabel('Flow Rate (vehicles/min)')
        
        plt.tight_layout()
        plt.savefig('traffic_analysis.png')
        plt.close()

def main():
    # For demonstration, we would use a video file
    # In production, this could be a live camera feed
    cap = cv2.VideoCapture('traffic_video.mp4')
    analyzer = TrafficAnalyzer()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        current_time = datetime.datetime.now()
        processed_frame, count, density = analyzer.analyze_frame(frame, current_time)
        
        # Display results
        cv2.putText(processed_frame, f"Vehicles: {count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(processed_frame, f"Density: {density:.6f}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('Traffic Analysis', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Process the collected data
    analyzer.calculate_flow_rate()
    analyzer.visualize_data()
    
    # Save the data
    analyzer.traffic_data.to_csv('traffic_data.csv', index=False)
    print("Analysis complete. Data saved to 'traffic_data.csv'")

if __name__ == "__main__":
    main()