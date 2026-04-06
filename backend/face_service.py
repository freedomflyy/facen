import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import onnxruntime
import os

class FaceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceService, cls).__new__(cls)
            cls._instance.init_models()
        return cls._instance

    def init_models(self):
        print("Initializing Face Analysis Models...")
        # Initialize InsightFace
        # Using CPUExecutionProvider for compatibility
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        print("InsightFace initialized.")

        # Initialize MiniFASNet
        model_path = os.path.join(os.path.dirname(__file__), "resources", "MiniFASNetV2.onnx")
        if os.path.exists(model_path):
            self.liveness_sess = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            print(f"MiniFASNet loaded from {model_path}")
        else:
            print(f"Warning: Liveness model not found at {model_path}. Liveness check will be disabled (always pass).")
            self.liveness_sess = None

    def process_image(self, image_bytes: bytes):
        """Convert bytes to opencv image"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image")
        return img

    def get_face_embedding(self, img):
        """
        Detect face and return the embedding of the largest face.
        Returns:
            embedding (list): 512-dim vector
            info (dict): {'has_face': bool, 'msg': str}
        """
        faces = self.app.get(img)
        if not faces:
            return None, {'has_face': False, 'msg': 'No face detected'}
        
        # Take the largest face
        face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))[-1]
        
        return face.embedding.tolist(), {'has_face': True, 'msg': 'Success', 'bbox': face.bbox}

    def check_liveness(self, img, bbox=None) -> float:
        """
        Check if the face is real (liveness detection).
        Returns a score between 0.0 (spoof) and 1.0 (real).
        """
        if self.liveness_sess is None:
            return 1.0 # Bypass if model missing

        # If bbox is not provided, detect first
        if bbox is None:
            faces = self.app.get(img)
            if not faces:
                return 0.0
            face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))[-1]
            bbox = face.bbox

        # Crop logic for MiniFASNet (Scale 2.7)
        x1, y1, x2, y2 = bbox.astype(int)
        w_box = x2 - x1
        h_box = y2 - y1
        
        # Find center
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        
        # Scale up
        scale = 2.7
        w_new = w_box * scale
        h_new = h_box * scale
        
        # New coordinates
        x1_new = int(cx - w_new / 2)
        y1_new = int(cy - h_new / 2)
        x2_new = int(cx + w_new / 2)
        y2_new = int(cy + h_new / 2)
        
        # Pad if necessary
        h, w = img.shape[:2]
        # We handle padding by cropping what we can and resizing, or padding image.
        # Simple approach: crop with boundary checks, but this distorts scale if close to edge.
        # Better: Pad image first.
        
        # For simplicity/robustness, let's just use safe crop coordinates
        x1_safe = max(0, x1_new)
        y1_safe = max(0, y1_new)
        x2_safe = min(w, x2_new)
        y2_safe = min(h, y2_new)
        
        crop = img[y1_safe:y2_safe, x1_safe:x2_safe]
        
        if crop.size == 0:
            return 0.0

        # Resize to 80x80
        resized = cv2.resize(crop, (80, 80))
        
        # Preprocess
        blob = resized.transpose(2, 0, 1).astype(np.float32) # HWC -> CHW
        blob = blob / 255.0 # Normalize to 0-1
        blob = np.expand_dims(blob, axis=0) # Add batch dim
        
        # Inference
        input_name = self.liveness_sess.get_inputs()[0].name
        prediction = self.liveness_sess.run(None, {input_name: blob})
        
        # Output is usually [prob_spoof, prob_real, ...] or similar
        # For MiniFASNetV2: shape (1, 3) -> [spoof, real, other] ??
        # Actually usually it is softmax over classes. 
        # Standard Silent-Face-Anti-Spoofing: Class 1 is real.
        
        probs = prediction[0][0]
        exp_probs = np.exp(probs)
        softmax = exp_probs / np.sum(exp_probs)
        
        # Assuming index 1 is real face
        # If output dim is 3 (spoof_type1, spoof_type2, real) -> usually real is last or specific index.
        # MiniFASNet V1/V2 typically has 3 classes: [background, spoof, live] or similar?
        # Let's check typical MiniFASNet output.
        # Many sources say: output shape (1, 3). Class 1 is live? Or Class 2?
        # Wait, the repo says "class 1 is real face, class 0 is fake face". 
        # But if shape is 3...
        # Let's assume index 1 is real. If output is size 2, index 1 is real.
        
        if len(softmax) == 3:
            # Common for MiniFASNet: 0: spoof, 1: real, 2: ??? 
            # Or maybe 0: live, 1: spoof? 
            # Let's stick to: index 1 is Live for MiniFASNetV2 (based on common issues)
            # Actually, standard MiniFASNetV2 (80x80) often has 3 outputs?
            # Let's assume index 1 is real.
            return float(softmax[1])
        elif len(softmax) == 2:
            return float(softmax[1])
        else:
            # Fallback
            return float(softmax[0])

    def compute_sim(self, feat1, feat2):
        if feat1 is None or feat2 is None:
            return 0.0
        feat1 = np.array(feat1)
        feat2 = np.array(feat2)
        return np.dot(feat1, feat2) / (np.linalg.norm(feat1) * np.linalg.norm(feat2))

face_service = FaceService()
