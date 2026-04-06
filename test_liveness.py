import cv2
import sys
import os
import numpy as np

# Add backend directory to path so we can import face_service
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from backend.face_service import face_service
except ImportError:
    # Try local import if running from backend dir
    sys.path.append(os.path.dirname(__file__))
    from backend.face_service import face_service

def test_liveness():
    print("=== Testing Liveness Detection ===")
    
    # Check if camera opens
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Press 'q' to quit, 's' to snapshot and check liveness.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow('Liveness Test - Press S to Check', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("\nChecking liveness...")
            # Detect face first to get bbox
            faces = face_service.app.get(frame)
            if not faces:
                print("No face detected!")
                continue
            
            # Sort by size
            faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
            face = faces[-1]
            bbox = face.bbox
            
            # Draw bbox
            debug_frame = frame.copy()
            x1, y1, x2, y2 = bbox.astype(int)
            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Check Liveness
            score = face_service.check_liveness(frame, bbox)
            print(f"Liveness Score: {score:.4f}")
            print(score)
            label = "Real" if score > 0.5 else "Fake"
            print(label)
            color = (0, 255, 0) if score > 0.5 else (0, 0, 255)
            
            cv2.putText(debug_frame, f"{label}: {score:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            cv2.imshow('Result', debug_frame)
            print(f"Result: {label} (Threshold: 0.5)")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_liveness()
