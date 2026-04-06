import cv2
import sys
import os
import time
import platform
import traceback
import numpy as np

# Add backend directory to path so we can import face_service
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from backend.face_service import face_service
except ImportError:
    # Try local import if running from backend dir
    sys.path.append(os.path.dirname(__file__))
    from backend.face_service import face_service


def _print_env_info():
    print("=== Environment Info ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Executable: {sys.executable}")
    print(f"Working dir: {os.getcwd()}")
    print(f"cv2 version: {cv2.__version__}")
    print(f"cv2 file: {cv2.__file__}")
    print("========================\n")


def _frame_stats(frame: np.ndarray):
    # Avoid expensive ops if frame is empty
    if frame is None:
        return {"is_none": True}
    return {
        "shape": frame.shape,
        "dtype": str(frame.dtype),
        "min": int(frame.min()) if frame.size else None,
        "max": int(frame.max()) if frame.size else None,
        "mean": float(frame.mean()) if frame.size else None,
        "contiguous": bool(frame.flags["C_CONTIGUOUS"]),
    }


def _clamp_bbox_xyxy(bbox, w, h):
    """
    bbox: [x1,y1,x2,y2] float/int
    returns: (bbox_int_np, info_dict)
    """
    x1, y1, x2, y2 = bbox.astype(int)

    original = (x1, y1, x2, y2)

    # clamp
    x1c = max(0, min(x1, w - 1))
    x2c = max(0, min(x2, w - 1))
    y1c = max(0, min(y1, h - 1))
    y2c = max(0, min(y2, h - 1))

    clamped = (x1c, y1c, x2c, y2c)

    invalid = (x2c <= x1c) or (y2c <= y1c)

    info = {
        "original": original,
        "clamped": clamped,
        "was_out_of_bounds": original != clamped,
        "invalid_after_clamp": invalid,
        "frame_w": w,
        "frame_h": h,
    }

    return np.array([x1c, y1c, x2c, y2c], dtype=np.int32), info


def test_liveness():
    _print_env_info()

    print("=== Testing Liveness Detection ===")

    cap = cv2.VideoCapture(0)
    print(f"[Camera] cap.isOpened(): {cap.isOpened()}")
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Camera properties (may return 0 or -1 depending on backend)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.getBackendName() if hasattr(cap, "getBackendName") else "unknown"
    print(f"[Camera] backend: {backend}")
    print(f"[Camera] CAP_PROP_FRAME_WIDTH: {width}")
    print(f"[Camera] CAP_PROP_FRAME_HEIGHT: {height}")
    print(f"[Camera] CAP_PROP_FPS: {fps}")
    print("Press 'q' to quit, 's' to snapshot and check liveness.\n")

    frame_idx = 0
    last_time = time.time()
    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            t1 = time.time()
            frame_idx += 1

            if not ret or frame is None:
                print(f"[Frame {frame_idx}] ret={ret}, frame=None -> break")
                break

            st = _frame_stats(frame)
            # Print some per-frame info, but not too spammy:
            # - every 30 frames, print stats
            # - you can change this to print every frame if you really want
            if frame_idx == 1 or frame_idx % 30 == 0:
                dt = t1 - last_time
                eff_fps = (30 / dt) if frame_idx % 30 == 0 and dt > 0 else None
                if frame_idx % 30 == 0:
                    last_time = t1
                print(
                    f"[Frame {frame_idx}] read_time_ms={(t1 - t0)*1000:.2f} "
                    f"shape={st['shape']} dtype={st['dtype']} "
                    f"min={st['min']} max={st['max']} mean={st['mean']:.2f} "
                    + (f"eff_fps≈{eff_fps:.2f}" if eff_fps else "")
                )

            cv2.imshow("Liveness Test - Press S to Check", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("[Key] q -> quit")
                break

            if key == ord("s"):
                print("\n[Key] s -> Checking liveness...")
                print(f"[Snapshot] frame_idx={frame_idx} {st}")

                # Face detection
                det_t0 = time.time()
                faces = face_service.app.get(frame)
                det_t1 = time.time()

                print(f"[Detect] faces_count={len(faces) if faces else 0} det_time_ms={(det_t1-det_t0)*1000:.2f}")

                if not faces:
                    print("[Detect] No face detected!")
                    continue

                # Print all faces info
                face_infos = []
                for i, f in enumerate(faces):
                    bbox = f.bbox
                    x1, y1, x2, y2 = bbox
                    area = float((x2 - x1) * (y2 - y1))
                    face_infos.append((area, i, bbox))
                face_infos.sort(reverse=True, key=lambda x: x[0])

                for rank, (area, i, bbox) in enumerate(face_infos, start=1):
                    print(f"[Face #{i}] rank_by_area={rank} area={area:.1f} bbox={bbox}")

                # pick largest
                _, best_i, _ = face_infos[0]
                face = faces[best_i]
                bbox = face.bbox

                h, w = frame.shape[:2]
                bbox_int, bbox_info = _clamp_bbox_xyxy(bbox, w, h)
                print(f"[BBox] {bbox_info}")

                if bbox_info["invalid_after_clamp"]:
                    print("[BBox] Invalid bbox after clamp -> skip")
                    continue

                # Draw bbox
                debug_frame = frame.copy()
                x1, y1, x2, y2 = bbox_int.tolist()
                cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Liveness check
                live_t0 = time.time()
                score = face_service.check_liveness(frame, bbox_int)
                live_t1 = time.time()

                print(f"[Liveness] score={score} type={type(score)} time_ms={(live_t1-live_t0)*1000:.2f}")

                # If score is numpy scalar, convert for formatting
                try:
                    score_f = float(score)
                except Exception:
                    score_f = score

                threshold = 0.5
                label = "Real" if score_f > threshold else "Fake"
                color = (0, 255, 0) if score_f > threshold else (0, 0, 255)

                cv2.putText(
                    debug_frame,
                    f"{label}: {score_f:.2f}",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    color,
                    2,
                )

                cv2.imshow("Result", debug_frame)
                print(f"[Result] label={label} threshold={threshold}\n")

    except KeyboardInterrupt:
        print("\n[Interrupt] KeyboardInterrupt")
    except Exception as e:
        print("\n[Exception] Unexpected error:")
        print(str(e))
        traceback.print_exc()
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[Cleanup] Camera released, windows destroyed.")


if __name__ == "__main__":
    test_liveness()