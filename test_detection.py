import cv2
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from backend.face_service import face_service
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from backend.face_service import face_service

def test_detection():
    print("=== Testing Face Detection & Counting ===")
    print("Press 'c' to count faces in current frame.")
    print("Press 'q' to quit.")

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow('Detection Test', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('c'):
            print("\nDetecting faces...")
            faces = face_service.app.get(frame)
            count = len(faces)
            print(f"Detected Faces: {count}")
            
            # Draw bboxes
            debug_frame = frame.copy()
            for face in faces:
                bbox = face.bbox.astype(int)
                cv2.rectangle(debug_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 255), 2)
                cv2.putText(debug_frame, f"Conf: {face.det_score:.2f}", (bbox[0], bbox[1]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            cv2.imshow('Detection Result', debug_frame)
            print("Check 'Detection Result' window.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_detection()
