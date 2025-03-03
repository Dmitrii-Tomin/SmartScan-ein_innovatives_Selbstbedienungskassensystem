import tkinter as tk
import threading
import cv2
from PIL import Image, ImageTk
from picamera2 import Picamera2
from ultralytics import YOLO
from collections import Counter
from stepper import move_stepper
import time

class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Object Detection GUI")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(self.main_frame)
        self.video_label.pack(pady=20, side=tk.LEFT)

        self.listbox_frame = tk.Frame(self.main_frame)
        self.listbox_frame.pack(side=tk.RIGHT, padx=20)

        self.listbox = tk.Listbox(self.listbox_frame, width=40, height=20, font=("Helvetica", 30))
        self.listbox.pack(pady=20)

        self.start_btn = tk.Button(root, text="Start Detection", command=self.start_detection)
        self.start_btn.pack()
        
        self.reset_btn = tk.Button(root, text="Reset Detection", command=self.reset_detection)
        self.reset_btn.pack()

        self.speed_label = tk.Label(root, text="Set Conveyor Speed:")
        self.speed_label.pack()

        self.speed = 0
        self.speed_buttons = []

        for speed in range(4):
            btn = tk.Button(root, text=f"Speed {speed}", command=lambda s=speed: self.set_speed(s))
            btn.pack(side=tk.LEFT, padx=5)
            self.speed_buttons.append(btn)

        self.running = False
        self.products_list = []
        self.previous_products_list = []

    def set_speed(self, speed):
        self.speed = speed
        print(f"Conveyor Speed Set To: {speed}")
        move_stepper(speed)
 
    def start_detection(self):
        if not self.running:
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            thread = threading.Thread(target=self.vision_loop, daemon=True)
            thread.start()
            
    def reset_detection(self):
        self.products_list = []
        self.current_tracker.clear()
        self.cost = 0
        self.counted_objects = 0

    def vision_loop(self):
        picam2 = Picamera2()
        picam2.preview_configuration.main.size = (1640, 1232)
        picam2.preview_configuration.main.format = "RGB888"
        picam2.configure("preview")
        
        picam2.set_controls({"ExposureTime": 20000})
        picam2.set_controls({"AeEnable": False})
        
        picam2.start()

        model = YOLO("best_ncnn_model3")
        
        pred_max, pred_min = 1000, -1000
        
        self.dictionary = {
            'spicy_noodles': 0.79,
            'chicken_noodles': 0.79,
            'beef_noodles': 0.79,
            'apple': 0.39,
            'banana': 0.49,
            'pringles': 1.29,
            'bionade': 1.24,
            'philadelphia': 0.95,
            'kitkat': 0.39,
            'twix': 0.59,
            'snickers': 0.59,
            'knoppers': 0.34
        }

        line_position = 800
        self.counted_objects = 0
        self.cost = 0
        previous_tracker = {}
        self.current_tracker = {}
        tracker = {}
        previous_time = 0
        current_time = 0
        min_travel = 0
        max_travel = 0
        
        while self.running:
            previous_time = current_time
            current_time = time.time()
            time_diffrence = current_time - previous_time
            
            frame = picam2.capture_array()
            results = model(frame)
            detections = results[0].boxes.xyxy
            classes = results[0].boxes.cls.to('cpu').tolist()
            confidences = results[0].boxes.conf

            if detections.numel() == 0:
                sorted_detections = detections
                sorted_classes = classes
                sorted_confidences = confidences  
            
            else:
                zipped = list(zip(detections, classes, confidences))
                sorted_zipped = sorted(zipped, key=lambda x: x[0][2])
                sorted_detections, sorted_classes, sorted_confidences = zip(*sorted_zipped)
            
                sorted_detections = list(sorted_detections)
                sorted_classes = list(sorted_classes)
                sorted_confidences = list(sorted_confidences)
                
            cv2.line(frame, (line_position, 0), (line_position, 1232), (0, 0, 255), 3)

            current_objects = {}
            
            if self.speed == 1:
                pred_max, pred_min = 540, 380
            elif self.speed == 2:
                pred_max, pred_min = 680, 480
            elif self.speed == 3:
                pred_max, pred_min = 1000, 700
            else:
                pred_max, pred_min = 1000, -1000
        

            for i, (box, obj, conf) in enumerate(zip(sorted_detections, sorted_classes, sorted_confidences)):
                x1, y1, x2, y2 = map(int, box)
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                confidence = float(conf)
                product = results[0].names[obj]
                price = self.dictionary.get(product, 0)
                

                if confidence < 0.5 or x1 < 10 or x2 > 1630:
                    continue
                
                #print(f"objects: {current_objects}", f"tracker: {current_tracker}")
                
                match_indx = None
                
                for indx, coords in previous_tracker.items():
                    prev_x, prev_y = coords['centroid']
                    x_diff = center_x - prev_x
                    y_diff = abs(center_y - prev_y)
                    tracker[indx] = {"x_diffrence": x_diff, "y_diffrence": y_diff}
                    
                    max_travel = time_diffrence * pred_max
                    min_travel = time_diffrence * pred_min
                    
                    if min_travel < x_diff < max_travel and y_diff <= 20:
                        match_indx = indx
                
                if match_indx is not None:
                    prev_x = previous_tracker[match_indx]["centroid"][0]
                    prev_y = previous_tracker[match_indx]["centroid"][1]
    

                    self.current_tracker[match_indx] = {"centroid": (center_x, center_y),
                                                   "counted": previous_tracker[match_indx]['counted']}
                    
                    #print(prev_x, center_x)

                    if not self.current_tracker[match_indx]["counted"] and prev_x < line_position and center_x >= line_position:
                        print("2")
                        self.counted_objects += 1
                        self.current_tracker[match_indx]["counted"] = True
                        self.products_list.append(product)
                        self.cost += price
                        self.cost = round(self.cost, 2)
                
                else:
                    indx = max(previous_tracker.keys(), default=0) + 1
                    self.current_tracker[indx] = {"centroid": (center_x, center_y),
                                             "counted": False,}
                    
                current_objects[match_indx] = (center_x, center_y)
                    
                    
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"Conf: {confidence:.2f} product: {product} indx: {match_indx}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
 
            print(f"tracker: {self.current_tracker} travel: {min_travel, max_travel}")
            previous_tracker = self.current_tracker

            if self.products_list != self.previous_products_list:
                self.previous_products_list = self.products_list.copy()
                self.update_list(self.dictionary)

            cv2.putText(frame, f"Count: {self.counted_objects} cost: {self.cost}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            move_stepper(self.speed)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            frame_resized = frame_image.resize((1040, 750))
            frame_tk = ImageTk.PhotoImage(frame_resized)

            self.video_label.config(image=frame_tk)
            self.video_label.image = frame_tk

            if cv2.waitKey(1) == ord("q"):
                break

        cv2.destroyAllWindows()
        move_stepper(0)

    def update_list(self, dictionary):
        self.listbox.delete(0, tk.END)

        product_counts = Counter(self.products_list)
        sorted_products = sorted(product_counts.items())

        for product, count in sorted_products:
            price = self.dictionary.get(product, 0)
            self.total_price = round(price * count, 2)
            item_text = f"{count}x {product.ljust(50)} ${self.total_price:.2f}"
            self.listbox.insert(tk.END, item_text)
            
        self.listbox.insert(tk.END, f"----------------------------------------------------------",
                            f"Total cost:   {self.cost:.2f}$")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisionApp(root)
    root.mainloop()

