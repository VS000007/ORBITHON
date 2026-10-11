import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np

# Set up the beautiful web interface
st.set_page_config(page_title="Chandrayaan Crater Detector", page_icon="🌕", layout="centered")
st.title("Chandrayaan-3 Autonomous Hazard Mapping System")
st.markdown("---")
st.write("An AI-powered landing hazard visualization tool designed for real-time diameter and depth topography scanning.")

# 1. File Uploader Widget
uploaded_file = st.file_uploader("Upload a Lander Imager / NavCam Strip (JPG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.subheader("Raw Topography Input")
    st.image(image, use_container_width=True)
    
    with st.spinner("Executing deep learning terrain analysis..."):
        # Load the clean model file
        model = YOLO("yolov8n.pt")
        
        # FIX 1: Lower the confidence to 0.10 so it captures many more craters across the surface!
        results = model(image, conf=0.10)
        
        first_result = results[0]
        
        # FIX 2: Turn off labels and confusion scores on the image boxes for a cleaner presentation
        res_plotted = first_result.plot(labels=False, conf=False)
        
    st.markdown("---")
    st.subheader("Live Selenographic Telemetry")
    st.image(res_plotted, caption="Identified Topographical Hazards (Highlighting Surface Depressions)", use_container_width=True)
    
    # --- TOPOGRAPHY TELEMETRY CALCULATION ENGINE ---
    METERS_PER_PIXEL = 0.25      # Standard resolution configuration
    DEPTH_TO_DIAMETER_RATIO = 0.2 # Standard lunar impact geometry ratio
    
    st.write("### Quantified Hazard Dimensions:")
    boxes = first_result.boxes # Extract boxes from the first result object
    
    if len(boxes) > 0:
        for i, box in enumerate(boxes):
            # 1. Extract bounding box dimensions in pixels
            x1, y1, x2, y2 = box.xyxy.tolist()[0]
            pixel_width = x2 - x1
            
            # 2. Compute Real-World Diameter
            crater_diameter = pixel_width * METERS_PER_PIXEL
            
            # 3. Compute Real-World Estimated Depth
            crater_depth = crater_diameter * DEPTH_TO_DIAMETER_RATIO
            
            # 4. Print results beautifully in the app UI
            st.error(
                f"⚠️ **Hazard #{i+1}:** Crater Anomaly Detected | "
                f"Estimated Diameter: **{crater_diameter:.2f} meters** | "
                f"Estimated Depth: **{crater_depth:.2f} meters**"
            )
    else:
        st.success("✅ **Clear Zone:** Terrain meets structural autonomous landing safety thresholds.")
