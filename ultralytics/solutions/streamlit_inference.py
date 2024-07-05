# Ultralytics YOLO 🚀, AGPL-3.0 license

import io

import cv2
import torch


def inference():
    # Scope imports for faster ultralytics package load speeds
    import streamlit as st
    from ultralytics import YOLO

    # Hide main menu style
    menu_style_cfg = """<style>MainMenu {visibility: hidden;}</style>"""

    # Main title of streamlit application
    main_title_cfg = """<div><h1 style="color:#FF64DA; text-align:center; font-size:40px; 
                             font-family: 'Archivo', sans-serif; margin-top:-50px;">
                    Ultralytics YOLOv8 Streamlit Application
                    </h1></div>"""

    # Subtitle of streamlit application
    sub_title_cfg = """<div><h4 style="color:#042AFF; text-align:center; 
                    font-family: 'Archivo', sans-serif; margin-top:-15px; margin-bottom:50px;">
                    Experience real-time object detection on your webcam with the power of Ultralytics YOLOv8! 🚀</h4>
                    </div>"""

    # Set html page configuration
    st.set_page_config(page_title="Ultralytics Streamlit App", layout="wide", initial_sidebar_state="auto")

    # Append the custom HTML
    st.markdown(menu_style_cfg, unsafe_allow_html=True)
    st.markdown(main_title_cfg, unsafe_allow_html=True)
    st.markdown(sub_title_cfg, unsafe_allow_html=True)

    # Add ultralytics logo in sidebar
    with st.sidebar:
        logo = "https://raw.githubusercontent.com/ultralytics/assets/main/logo/Ultralytics_Logotype_Original.svg"
        st.image(logo, width=250)

    # Add elements to vertical setting menu
    st.sidebar.title("User Configuration")

    # Add video source selection dropdown
    source = st.sidebar.selectbox(
        "Video",
        ("webcam", "video"),
    )

    vid_file_name = ""
    if source == "video":
        vid_file = st.sidebar.file_uploader("Upload Video File", type=["mp4", "mov", "avi", "mkv"])
        if vid_file is not None:
            g = io.BytesIO(vid_file.read())  # BytesIO Object
            vid_location = "ultralytics.mp4"
            with open(vid_location, "wb") as out:  # Open temporary file as bytes
                out.write(g.read())  # Read bytes into file
            vid_file_name = "ultralytics.mp4"
    elif source == "webcam":
        vid_file_name = 0

    # Add dropdown menu for model selection
    yolov8_model = st.sidebar.selectbox(
        "Model",
        (
            "YOLOv8n",
            "YOLOv8s",
            "YOLOv8m",
            "YOLOv8l",
            "YOLOv8x",
            "YOLOv8n-Seg",
            "YOLOv8s-Seg",
            "YOLOv8m-Seg",
            "YOLOv8l-Seg",
            "YOLOv8x-Seg",
            "YOLOv8n-Pose",
            "YOLOv8s-Pose",
            "YOLOv8m-Pose",
            "YOLOv8l-Pose",
            "YOLOv8x-Pose",
        ),
    )
    conf_thres = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.25, 0.01)
    nms_thres = st.sidebar.slider("NMS Threshold", 0.0, 1.0, 0.45, 0.01)

    col1, col2 = st.columns(2)
    org_frame = col1.empty()
    ann_frame = col2.empty()

    if st.sidebar.button("Start"):
        model = YOLO(f"{yolov8_model.lower()}.pt")  # Load the yolov8 model
        videocapture = cv2.VideoCapture(vid_file_name)  # Capture the video

        if not videocapture.isOpened():
            st.error("Could not open webcam.")

        stop_button = st.button("Stop")  # Button to stop the inference
        # execute code until file closed
        while videocapture.isOpened():
            success, frame = videocapture.read()
            if not success:
                st.warning("Failed to read frame from webcam. Please make sure the webcam is connected properly.")
                break

            # Store model predictions
            results = model(frame, conf=float(conf_thres), iou=float(nms_thres))
            annotated_frame = results[0].plot()  # Add annotations on frame

            # display frame
            org_frame.image(frame, channels="BGR")
            ann_frame.image(annotated_frame, channels="BGR")

            if stop_button:
                videocapture.release()  # Release the capture
                torch.cuda.empty_cache()  # Clear CUDA memory
                st.stop()  # Stop streamlit app

        # Release the capture
        videocapture.release()

    # Clear CUDA memory
    torch.cuda.empty_cache()

    # Destroy window
    cv2.destroyAllWindows()


# Main function call
if __name__ == "__main__":
    inference()
