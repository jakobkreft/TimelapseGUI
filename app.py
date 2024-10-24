import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import os
import shutil

class TimelapseApp:
    def __init__(self, master):
        self.master = master
        master.title("Timelapse Capture")
        self.recording = False
        self.interval = 5  # default interval in seconds
        self.framerate = 30  # default framerate for output video
        self.frame_count = 0
        self.image_folder = "timelapse_images"
        self.camera_index = 0
        self.preview_running = False
        self.cap = None
        self.start_time = None

        # Set default window size
        self.master.geometry("800x600")

        # Camera selection
        self.camera_label = ttk.Label(master, text="Camera Index:")
        self.camera_label.pack()
        self.camera_entry = ttk.Entry(master)
        self.camera_entry.insert(0, "0")
        self.camera_entry.pack()

        self.set_camera_button = ttk.Button(master, text="Set Camera", command=self.set_camera)
        self.set_camera_button.pack()

        # Interval and framerate
        self.interval_label = ttk.Label(master, text="Interval (seconds):")
        self.interval_label.pack()
        self.interval_entry = ttk.Entry(master)
        self.interval_entry.insert(0, "5")
        self.interval_entry.pack()

        self.framerate_label = ttk.Label(master, text="Framerate (fps):")
        self.framerate_label.pack()
        self.framerate_entry = ttk.Entry(master)
        self.framerate_entry.insert(0, "30")
        self.framerate_entry.pack()

        # Record/Stop button
        self.record_button = ttk.Button(master, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack()

        # Recording duration label
        self.duration_label = ttk.Label(master, text="")
        self.duration_label.pack()

        # Final video length label
        self.video_length_label = ttk.Label(master, text="")
        self.video_length_label.pack()

        # Close button
        self.close_button = ttk.Button(master, text="Close", command=self.on_closing)
        self.close_button.pack()

        # Image preview
        self.image_label = ttk.Label(master)
        self.image_label.pack()

        # Start preview
        self.set_camera()
        self.start_preview()

    def set_camera(self):
        camera_index = int(self.camera_entry.get())
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print(f"Cannot open camera {camera_index}")
        else:
            print(f"Camera {camera_index} opened.")

    def start_preview(self):
        if not self.preview_running:
            self.preview_running = True
            self.update_preview()

    def get_window_size(self):
        # Ensure that the window dimensions are greater than zero
        width = self.master.winfo_width()
        height = self.master.winfo_height() - 200  # Subtracting space for controls
        if width <= 0 or height <= 0:
            width = 640
            height = 480
        return (width, height)

    def resize_image_to_fit(self, img, window_size):
        window_width, window_height = window_size
        img_width, img_height = img.size

        # Calculate the scaling factor to maintain aspect ratio
        scale = min(window_width / img_width, window_height / img_height)

        # Compute new image size
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # Resize the image
        resized_img = img.resize((new_width, new_height), Image.ANTIALIAS)
        return resized_img

    def update_preview(self):
        if self.preview_running:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)
                    # Resize to fit the window while maintaining aspect ratio
                    window_size = self.get_window_size()
                    img = self.resize_image_to_fit(img, window_size)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.image_label.imgtk = imgtk
                    self.image_label.configure(image=imgtk)
            self.master.after(30, self.update_preview)

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
            self.record_button.config(text="Start Recording")
            self.duration_label.config(text="")
            self.video_length_label.config(text="")
            # Restart the preview
            self.start_preview()
        else:
            self.start_recording()
            self.record_button.config(text="Stop Recording")

    def start_recording(self):
        self.interval = float(self.interval_entry.get())
        self.framerate = float(self.framerate_entry.get())
        self.recording = True
        self.frame_count = 0
        self.start_time = time.time()
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        else:
            shutil.rmtree(self.image_folder)
            os.makedirs(self.image_folder)
        # Stop the preview
        self.preview_running = False
        threading.Thread(target=self.record).start()
        self.update_duration()

    def record(self):
        while self.recording:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    filename = os.path.join(self.image_folder, f"frame_{self.frame_count:05d}.jpg")
                    cv2.imwrite(filename, frame)
                    self.frame_count +=1

                    # Update image in GUI with the last captured frame
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)
                    # Resize to fit the window while maintaining aspect ratio
                    window_size = self.get_window_size()
                    img = self.resize_image_to_fit(img, window_size)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.image_label.imgtk = imgtk
                    self.image_label.configure(image=imgtk)

                    # Update final video length
                    video_seconds = self.frame_count / self.framerate
                    video_minutes = int(video_seconds // 60)
                    video_seconds = int(video_seconds % 60)
                    self.video_length_label.config(text=f"Final Video Length: {video_minutes:02d}:{video_seconds:02d}")

                else:
                    print("Failed to grab frame")
            else:
                print("Camera not available")
            time.sleep(self.interval)

    def update_duration(self):
        if self.recording:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            self.duration_label.config(text=f"Recording for {minutes:02d}:{seconds:02d}")
            self.master.after(1000, self.update_duration)

    def stop_recording(self):
        self.recording = False
        self.create_video()

    def create_video(self):
        image_files = [os.path.join(self.image_folder, f) for f in sorted(os.listdir(self.image_folder)) if f.endswith('.jpg')]
        if not image_files:
            print("No images to create video.")
            return
        # Get frame size
        frame = cv2.imread(image_files[0])
        height, width, layers = frame.shape
        video_name = "timelapse.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(video_name, fourcc, self.framerate, (width, height))

        for img_file in image_files:
            img = cv2.imread(img_file)
            video.write(img)

        video.release()
        print(f"Timelapse video saved as {video_name}")

        # Optionally, clean up images
        shutil.rmtree(self.image_folder)

    def on_closing(self):
        self.preview_running = False
        self.recording = False
        if self.cap is not None:
            self.cap.release()
        self.master.destroy()

root = tk.Tk()
app = TimelapseApp(root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.mainloop()

