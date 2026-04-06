<template>
  <div class="liveness-container">
    <div class="camera-wrapper">
      <video ref="video" autoplay muted playsinline class="video-feed"></video>
      <canvas ref="overlay" class="overlay-canvas"></canvas>
      
      <!-- 引导遮罩 -->
      <div class="guide-mask" :class="{ 'success': isActionCompleted }">
        <div class="message-box" v-if="!isActionCompleted"> <!-- 完成后隐藏提示框，只显示成功状态 -->
          <h3 v-if="!isModelLoaded">正在加载模型...</h3>
          <template v-else>
            <h3 v-if="!isFaceDetected">请正对屏幕</h3>
            <h3 v-else>{{ currentInstruction }}</h3>
          </template>
        </div>
        <div v-else class="success-overlay">
             <div class="success-icon">✔</div>
             <h3>验证通过</h3>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as faceapi from 'face-api.js'

const emit = defineEmits(['success', 'fail'])

const video = ref(null)
const overlay = ref(null)
const isModelLoaded = ref(false)
const isFaceDetected = ref(false)
const isActionCompleted = ref(false)
const currentInstruction = ref('请眨眼')
const currentAction = ref('mouth') // 'mouth', 'nod', 'shake'

let detectionInterval = null
let mouthCounter = 0
let headPoseCounter = 0
let lastHeadPose = null

// 阈值配置
const MAR_THRESHOLD = 0.5  // 嘴巴张开阈值
const HEAD_YAW_THRESHOLD = 15 // 摇头角度 (度)
const HEAD_PITCH_THRESHOLD = 15 // 点头角度 (度)

onMounted(async () => {
  await loadModels()
  await startCamera()
  randomizeAction()
  startDetection()
})

onUnmounted(() => {
  stopCamera()
  if (detectionInterval) clearInterval(detectionInterval)
})

const loadModels = async () => {
  try {
    const MODEL_URL = '/models'
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL)
    ])
    isModelLoaded.value = true
  } catch (e) {
    console.error("模型加载失败", e)
    emit('fail', '模型加载失败')
  }
}

const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: {} })
    video.value.srcObject = stream
  } catch (e) {
    emit('fail', '无法获取摄像头权限')
  }
}

const stopCamera = () => {
  const stream = video.value?.srcObject
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
}

const randomizeAction = () => {
  const r = Math.random()
  if (r < 0.33) {
    currentAction.value = 'mouth'
    currentInstruction.value = '请张嘴 (Open Mouth)'
  } else if (r < 0.66) {
    currentAction.value = 'nod'
    currentInstruction.value = '请点头 (Nod Head)'
  } else {
    currentAction.value = 'shake'
    currentInstruction.value = '请摇头 (Shake Head)'
  }
}

const startDetection = () => {
  detectionInterval = setInterval(async () => {
    if (!video.value || !isModelLoaded.value) return

    // Detect
    const detection = await faceapi.detectSingleFace(video.value, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()

    if (detection) {
      isFaceDetected.value = true
      const landmarks = detection.landmarks
      
      // Match dimensions to video
      const dims = faceapi.matchDimensions(overlay.value, video.value, true)
      // Resize detection results to match canvas
      const resized = faceapi.resizeResults(detection, dims)
      
      // Draw landmarks for debug/feedback
      // faceapi.draw.drawFaceLandmarks(overlay.value, resized)
      
      // Use resized landmarks for calculations to match visual
      checkAction(resized.landmarks)
    } else {
      isFaceDetected.value = false
    }
  }, 100)
}

const checkAction = (landmarks) => {
  if (isActionCompleted.value) return

  // const leftEye = landmarks.getLeftEye()
  // const rightEye = landmarks.getRightEye()
  const mouth = landmarks.getMouth()
  
  // Estimate Head Pose
  // Use nose and face outline to estimate pose roughly
  const nose = landmarks.getNose()
  const jaw = landmarks.getJawOutline()
  
  // Yaw: Nose X relative to Jaw Center X
  const noseTop = nose[0]
  const jawLeft = jaw[0]
  const jawRight = jaw[16]
  const faceWidth = dist(jawLeft, jawRight)
  const noseX = noseTop.x
  const centerX = (jawLeft.x + jawRight.x) / 2
  // Yaw ratio: (noseX - centerX) / faceWidth
  // range approx -0.5 to 0.5?
  const yawRatio = (noseX - centerX) / faceWidth
  const yawAngle = yawRatio * 90 * 2 // Crude approximation
  
  // Pitch: Nose Y relative to Eye/Jaw Y?
  // Use vertical distance ratios
  // Distance from NoseTop to Chin vs Eye to NoseTop
  const chin = jaw[8]
  const noseBottom = nose[6]
  const noseBridge = nose[0]
  
  // Crude pitch: nose length projected
  // Or simply: relative position of nose tip between eyes and mouth
  // Let's use simple logic:
  // Nod: Nose moves DOWN then UP. Pitch changes.
  // Pitch approx: (noseBottom.y - noseBridge.y) / faceHeight ?
  // Or better: Distance from NoseTop to Chin.
  // When looking DOWN, chin gets closer to nose? No.
  // When looking DOWN, whole face moves down? No.
  // When looking DOWN, distance between Eyes and Nose decreases?
  // Let's rely on Y movement of nose tip relative to fixed frame? No user moves.
  
  // Let's use a simpler heuristic for Nod:
  // Compare nose Y position relative to face bounding box center?
  // Or just vertical movement of nose tip over time?
  // If we track nose.y...
  
  // Better Head Pose from Landmarks:
  // Using 68 points PnP is best but complex in JS without OpenCV.
  // Simple heuristic for Pitch:
  // Ratio of (NoseTop to Chin) / (NoseTop to NoseBottom) ?
  
  // Let's use simple movement tracking for Nod/Shake
  
  if (currentAction.value === 'mouth') {
    const mar = getMAR(mouth)
    if (mar > MAR_THRESHOLD) {
      mouthCounter++
    } else {
      if (mouthCounter > 1) {
        completeAction()
      }
      mouthCounter = 0
    }
  } else if (currentAction.value === 'shake') {
    // Detect Yaw change
    // If yaw goes > +Threshold then < -Threshold (or vice versa)
    if (!lastHeadPose) lastHeadPose = { yaw: yawAngle, pitch: 0, time: Date.now() }
    
    // Check for significant movement
    const yawDiff = yawAngle - lastHeadPose.yaw
    if (Math.abs(yawAngle) > HEAD_YAW_THRESHOLD) {
       headPoseCounter++
    }
    
    if (headPoseCounter > 5) { // Sustained turn
       completeAction()
    }
    
  } else if (currentAction.value === 'nod') {
      // Nod detection
      // Use nose tip Y movement
      const noseY = nose[6].y
      if (!lastHeadPose) lastHeadPose = { y: noseY, time: Date.now(), state: 'center' }
      
      const diff = noseY - lastHeadPose.y
      // If moves down significantly then up
      // Or just check if nose position is significantly lower than initial 'center' (looking down)
      // Normalizing by face height
      const faceHeight = dist(jaw[8], nose[0]) * 2
      const moveRatio = diff / faceHeight
      
      if (Math.abs(moveRatio) > 0.1) { // 10% movement
          headPoseCounter++
      }
      
      if (headPoseCounter > 5) {
          completeAction()
      }
  }
}

const completeAction = () => {
  isActionCompleted.value = true
  
  // 立即停止检测循环，防止重复触发
  if (detectionInterval) {
    clearInterval(detectionInterval)
    detectionInterval = null
  }
  
  // 延迟一点抓拍，防止拍到闭眼或张嘴过大
  setTimeout(() => {
    captureImage()
    // 抓拍完成后停止摄像头，冻结画面
    stopCamera() 
  }, 500) 
}

const captureImage = () => {
  const canvas = document.createElement('canvas')
  canvas.width = video.value.videoWidth
  canvas.height = video.value.videoHeight
  canvas.getContext('2d').drawImage(video.value, 0, 0)
  
  canvas.toBlob((blob) => {
    emit('success', blob)
  }, 'image/jpeg', 0.95)
}

// Eye Aspect Ratio
const getEAR = (eye) => {
  const A = dist(eye[1], eye[5])
  const B = dist(eye[2], eye[4])
  const C = dist(eye[0], eye[3])
  return (A + B) / (2.0 * C)
}

// Mouth Aspect Ratio
const getMAR = (mouth) => {
  // face-api mouth points: 0-19 (20 points)
  // Outer lip: 0-11
  // Inner lip: 12-19
  // Simple MAR: height / width of outer lip
  // Top lip bottom: 14 (idx 14 in 20pts? No, face-api uses 68 point scheme mapped)
  // getMouth() returns 20 points.
  // 0-11 outer, 12-19 inner.
  // Height: (2-10) + (3-9) + (4-8) ... let's simplify
  // Use Inner Height / Inner Width for openness
  
  const p = mouth
  // Inner Height: dist(13, 19) + dist(14, 18) + dist(15, 17) -- approx
  // Let's use outer lip height vs width
  const A = dist(p[2], p[10]) // Upper vs Lower
  const B = dist(p[3], p[9])
  const C = dist(p[4], p[8])
  
  const width = dist(p[0], p[6])
  return (A + B + C) / (3.0 * width)
}

const dist = (p1, p2) => {
  return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2))
}
</script>

<style scoped>
.liveness-container {
  position: relative;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}
.camera-wrapper {
  position: relative;
  padding-top: 75%; /* 4:3 Aspect Ratio */
}
.video-feed {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* Mirror */
}
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.guide-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 40px;
  pointer-events: none;
}
.message-box {
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 12px 24px;
  border-radius: 30px;
  text-align: center;
  backdrop-filter: blur(4px);
}
.success-text {
  color: #67c23a;
  font-weight: bold;
}
.success-overlay {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #67c23a;
    background: rgba(0,0,0,0.4);
    width: 100%;
}
.success-icon {
    font-size: 48px;
    border: 3px solid #67c23a;
    border-radius: 50%;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
}
</style>
