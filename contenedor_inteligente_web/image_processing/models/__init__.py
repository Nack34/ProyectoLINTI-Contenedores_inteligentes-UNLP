import os
from ultralytics import YOLO

trimmer_name = "best.pt"

trimmer_model = os.path.join(os.path.dirname(__file__), os.path.join("trimmer", trimmer_name))

def load_trimmer_model():
    model = YOLO(trimmer_model)
    
    for m in model.modules():
        # Add this check:
        if hasattr(m, 'bn') and m.bn is not None:
            m.bn.track_running_stats = False
            
    return model