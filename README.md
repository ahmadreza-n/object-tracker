# Real-Time Object Tracking System

This project implements a real-time object tracking system using a pan-tilt camera. The system integrates deep neural networks for object detection with operator-selectable tracking algorithms (CSRT and KCF) for efficient and accurate object tracking.

## Key Features

- **Real-Time Object Detection and Tracking:**
  Utilizes Python and the OpenCV library for image processing.

- **Microcontroller Integration:**
  Designed to compute control signals and command motors via serial communication.

- **Performance Monitoring:**
  Real-time error calculation and system monitoring.

- **Scalable Design:**
  Suitable for applications like video surveillance and object tracking, balancing accuracy, speed, and cost-effectiveness.

## Dependencies

The project relies on the following technologies:

- **Programming Languages:**

  - Python (for image processing and control logic)

- **Libraries and Frameworks:**

  - OpenCV: For object detection and tracking

- **Hardware Integration:**

  - Serial communication to interface with microcontroller-based motor control

## How to Run

1. **Set up the environment:**

   - Ensure Python is installed and create a virtual environment.
   - Install required Python packages

2. **Connect the Hardware:**

   - Attach the pan-tilt camera and ensure the microcontroller is correctly configured.

3. **Run the Application:**

   - Execute the main script:
     ```bash
     python app.py
     ```
     or
     ```bash
     python app.py --help
     ```

4. **Monitor Performance:**

   - Use the real-time monitoring interface to observe tracking accuracy and control signals.

## Applications

This project demonstrates expertise in computer vision, embedded systems, and real-time system development. It is particularly suitable for:

- Video surveillance
- Object tracking in dynamic environments

## Acknowledgments

This project was completed under the supervision of **Dr. Khosravi** and **Dr. Menhaj** at **Amirkabir University of Technology**. It showcases the integration of software and hardware systems to achieve scalable and efficient real-time object tracking, reflecting a combination of skills in computer vision, embedded systems, and real-time control.

## Hardware Setup

Below is an image of the Sony Eye Cam mounted on a custom-designed bracket with two SG90 servo motors. The system operates by connecting the camera to a laptop for image processing. The laptop calculates the tracking error and sends control signals to a WEMOS D1 R1 board, which adjusts the motors to align the camera with the target object.

![image](https://github.com/user-attachments/assets/82c40972-0b1b-41da-9c32-c9be65733ccc)

