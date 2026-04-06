<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>课堂人脸签到系统</h2>
      <el-tabs v-model="activeTab" class="custom-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-width="0" size="large">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="请输入用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">登 录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
           <el-form :model="registerForm" label-width="0" size="large">
            <el-form-item>
              <el-input v-model="registerForm.username" placeholder="设置用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.password" type="password" placeholder="设置密码" :prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-select v-model="registerForm.role" placeholder="选择身份" style="width: 100%">
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
            
            <!-- 学生专属字段 -->
            <template v-if="registerForm.role === 'student'">
              <el-form-item>
                <el-input v-model="registerForm.full_name" placeholder="真实姓名 (如: 张三)" />
              </el-form-item>
              <el-form-item>
                <el-input v-model="registerForm.student_id" placeholder="学号 (如: 2021001)" />
              </el-form-item>
              <el-form-item>
                <el-select 
                  v-model="registerForm.class_id" 
                  placeholder="选择班级" 
                  filterable 
                  style="width: 100%"
                >
                  <el-option 
                    v-for="c in classList" 
                    :key="c.id" 
                    :label="c.name + ' (' + c.major + ')'" 
                    :value="c.id" 
                  />
                </el-select>
              </el-form-item>
              <el-form-item>
                  <div style="display: flex; gap: 10px; width: 100%">
                    <el-upload
                        class="avatar-uploader"
                        action="#"
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="handlePhotoChange"
                        accept="image/*"
                        style="flex: 1"
                      >
                        <el-button :icon="Upload" style="width: 100%">上传照片</el-button>
                      </el-upload>
                      <el-button :icon="Camera" type="primary" plain @click="openCamera" style="flex: 1">拍照</el-button>
                  </div>
                  <div v-if="capturedImage || registerForm.photo" class="preview-box">
                      <img :src="capturedImage || (registerForm.photo ? getObjectURL(registerForm.photo) : '')" class="avatar-preview" />
                      <span class="preview-text">已选择照片</span>
                  </div>
               </el-form-item>
             </template>
             <el-button type="success" @click="handleRegister" :loading="loading" style="width: 100%">注 册</el-button>
           </el-form>
         </el-tab-pane>
       </el-tabs>
     </el-card>

     <!-- 拍照弹窗 -->
    <el-dialog v-model="showCamera" title="拍照录入" width="500px" @close="stopCamera" append-to-body>
      <div class="camera-container">
        <video ref="video" autoplay playsinline muted class="camera-video"></video>
        <canvas ref="canvas" style="display: none;"></canvas>
      </div>
      <template #footer>
        <el-button @click="stopCamera">取消</el-button>
        <el-button type="primary" @click="takePhoto">拍照确认</el-button>
      </template>
    </el-dialog>
   </div>
 </template>

 <script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Upload, Camera } from '@element-plus/icons-vue'

const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)
const showCamera = ref(false)
const video = ref(null)
const canvas = ref(null)
const stream = ref(null)
const capturedImage = ref(null)

const loginForm = ref({
  username: '',
  password: ''
})

const registerForm = ref({
  username: '',
  password: '',
  role: 'student',
  full_name: '',
  student_id: '',
  class_id: null,
  photo: null
})

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', loginForm.value.username)
    formData.append('password', loginForm.value.password)
    
    const response = await axios.post('/api/token', formData)
    const { access_token, role } = response.data
    
    localStorage.setItem('token', access_token)
    localStorage.setItem('role', role)
    localStorage.setItem('username', loginForm.value.username)
    
    ElMessage.success('登录成功')
    if (role === 'teacher') {
      router.push('/teacher')
    } else if (role === 'admin') {
      router.push('/admin')
    } else {
      router.push('/student')
    }
  } catch (error) {
    ElMessage.error('登录失败: ' + (error.response?.data?.detail || '用户名或密码错误'))
  } finally {
    loading.value = false
  }
}

const classList = ref([])

onMounted(async () => {
    try {
        const res = await axios.get('/api/classes')
        classList.value = res.data
    } catch (e) {
        console.error("Failed to fetch classes")
    }
})

const handleRegister = async () => {
  if (!registerForm.value.username || !registerForm.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (registerForm.value.role === 'student' && !registerForm.value.photo) {
      ElMessage.warning('请上传人脸照片')
      return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', registerForm.value.username)
    formData.append('password', registerForm.value.password)
    formData.append('role', registerForm.value.role)
    
    if (registerForm.value.role === 'student') {
      formData.append('full_name', registerForm.value.full_name)
      formData.append('student_id', registerForm.value.student_id)
      formData.append('class_id', registerForm.value.class_id)
      formData.append('file', registerForm.value.photo)
    }

    await axios.post('/api/register', formData)
    ElMessage.success('注册成功！请登录')
    activeTab.value = 'login'
  } catch (error) {
    ElMessage.error('注册失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const handlePhotoChange = (file) => {
    registerForm.value.photo = file.raw
    capturedImage.value = null // 清除拍照预览，优先显示上传的
}

const getObjectURL = (file) => {
    return URL.createObjectURL(file)
}

const openCamera = async () => {
    showCamera.value = true
    try {
        stream.value = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
        // nextTick
        setTimeout(() => {
            if (video.value) video.value.srcObject = stream.value
        }, 100)
    } catch (e) {
        ElMessage.error("无法访问摄像头")
        showCamera.value = false
    }
}

const stopCamera = () => {
    if (stream.value) {
        stream.value.getTracks().forEach(t => t.stop())
        stream.value = null
    }
    showCamera.value = false
}

const takePhoto = () => {
    const ctx = canvas.value.getContext('2d')
    canvas.value.width = video.value.videoWidth
    canvas.value.height = video.value.videoHeight
    ctx.drawImage(video.value, 0, 0)
    
    canvas.value.toBlob((blob) => {
        // Create a File object from Blob
        const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" })
        registerForm.value.photo = file
        capturedImage.value = URL.createObjectURL(blob)
        stopCamera()
    }, 'image/jpeg')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
  font-weight: 600;
}
:deep(.el-tabs__nav) {
  width: 100%;
}
:deep(.el-tabs__item) {
  width: 50%;
  text-align: center;
}
.preview-box {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #f5f7fa;
    padding: 8px;
    border-radius: 4px;
}
.avatar-preview {
    width: 40px;
    height: 40px;
    border-radius: 4px;
    object-fit: cover;
}
.camera-video {
    width: 100%;
    border-radius: 8px;
    background: #000;
}
</style>
