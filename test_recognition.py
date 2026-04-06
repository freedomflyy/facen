import cv2
import sys
import os
import numpy as np
import json

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from backend.face_service import face_service
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from backend.face_service import face_service

def test_recognition():
    print("=== Testing Face Recognition (Embedding) ===")
    print("Step 1: Register a face (Press 'r')")
    print("Step 2: Verify against registered face (Press 'v')")
    print("Press 'q' to quit.")

    cap = cv2.VideoCapture(0)
    registered_emb = None

    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow('Recognition Test', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('r'):
            print("\nRegistering face...")
            emb, info = face_service.get_face_embedding(frame)
            if emb:
                registered_emb = emb
                print("Face registered successfully!")
                print(f"Embedding vector length: {len(emb)}")
            else:
                print(f"Registration failed: {info['msg']}")

        elif key == ord('v'):
            if registered_emb is None:
                print("\nPlease register a face first (Press 'r')")
                continue
            
            print("\nVerifying face...")
            current_emb, info = face_service.get_face_embedding(frame)
            if current_emb:
                sim = face_service.compute_sim(registered_emb, current_emb)
                print(f"Similarity Score: {sim:.4f}")
                
                is_match = sim > 0.4
                result = "MATCH" if is_match else "NO MATCH"
                print(f"Result: {result}")
            else:
                print(f"Verification failed: {info['msg']}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_recognition()
