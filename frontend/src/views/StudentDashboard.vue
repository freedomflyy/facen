<template>
  <div class="dashboard-container">
    <el-header class="header">
      <div class="header-content">
        <div class="logo">
           <el-icon :size="24" style="margin-right: 8px"><UserFilled /></el-icon>
           <h2>学生签到端</h2>
        </div>
        <div class="header-right">
             <el-button type="primary" link @click="showHistory = true">历史记录</el-button>
             <el-button type="danger" plain size="small" @click="logout">退出登录</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="main-content">
      <div class="center-wrapper">
        <!-- 历史记录抽屉 -->
        <el-drawer v-model="showHistory" title="我的签到记录" size="400px">
             <el-table :data="historyList" stripe style="width: 100%">
                <el-table-column prop="session_name" label="课程" />
                <el-table-column prop="check_in_time" label="时间" width="100">
                    <template #default="scope">
                        {{ new Date(scope.row.check_in_time).toLocaleTimeString() }}
                    </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                     <template #default="scope">
                        <el-tag size="small" type="success">已签到</el-tag>
                    </template>
                </el-table-column>
             </el-table>
        </el-drawer>

        <!-- 步骤1：输入签到码 -->
        <transition name="el-fade-in-linear">
          <div v-if="!currentStep" class="step-card">
            <el-card shadow="always">
              <div class="card-header">
                <h3>加入签到</h3>
                <p class="subtitle">请输入教师提供的 6 位签到码</p>
              </div>
              <div class="input-area">
                 <el-input 
                  v-model="sessionCode" 
                  placeholder="请输入签到码" 
                  size="large" 
                  maxlength="6"
                  show-word-limit
                  class="code-input"
                  @keyup.enter="verifyCode"
                >
                  <template #prefix>
                    <el-icon><Key /></el-icon>
                  </template>
                </el-input>
                <el-button type="primary" size="large" @click="verifyCode" style="width: 100%; margin-top: 20px;">
                  下一步
                </el-button>
              </div>
            </el-card>
          </div>
        </transition>

        <!-- 步骤2：人脸验证 -->
        <transition name="el-fade-in-linear">
          <div v-if="currentStep === 'camera'" class="step-card camera-mode">
            <el-card shadow="always" :body-style="{ padding: '0px' }">
              <div class="camera-header">
                <h3>{{ sessionData.name }} - 人脸验证</h3>
                <div class="session-info">
                   <p>
                     <el-icon><Clock /></el-icon> 
                     截止时间: {{ new Date(sessionData.end_time).toLocaleTimeString() }}
                   </p>
                   <p v-if="sessionData.latitude">
                     <el-icon><Location /></el-icon> 
                     需在签到点 {{ sessionData.radius }}米范围内
                   </p>
                </div>
                <div v-if="sessionData.latitude && currentGeo" class="geo-info">
                    <p>当前定位: {{ currentGeo.latitude.toFixed(5) }}, {{ currentGeo.longitude.toFixed(5) }}</p>
                </div>
              </div>
              
              <div class="camera-view">
                <!-- 活体检测组件 -->
                <LivenessDetection 
                  v-if="currentStep === 'camera'"
                  @success="handleLivenessSuccess"
                  @fail="handleLivenessFail"
                />
              </div>

              <div class="camera-footer">
                <el-button @click="resetStep">取消</el-button>
                <el-button type="info" size="large" disabled>
                  <el-icon style="margin-right: 8px"><Camera /></el-icon>
                  请配合完成动作
                </el-button>
              </div>
            </el-card>
          </div>
        </transition>
      </div>
    </el-main>
  </div>
</template>

<script setup>
import { ref, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, Key, Camera, Clock, Location } from '@element-plus/icons-vue'
import LivenessDetection from '../components/LivenessDetection.vue'

const router = useRouter()
const sessionCode = ref('')
const currentStep = ref(null) // null | 'camera'
const loading = ref(false)
const sessionData = ref(null)
const showHistory = ref(false)
const historyList = ref([])
const currentGeo = ref(null)

const token = localStorage.getItem('token')
const config = { headers: { Authorization: `Bearer ${token}` } }

// Fetch history when drawer opens or component mounts
const fetchHistory = async () => {
    try {
        const res = await axios.get('/api/attendance/me', config)
        historyList.value = res.data
    } catch (e) {
        console.error(e)
    }
}

watch(showHistory, (val) => {
    if (val) fetchHistory()
})

const verifyCode = async () => {
  if (!sessionCode.value || sessionCode.value.length !== 6) {
    ElMessage.warning('请输入6位签到码')
    return
  }
  
  // Get Geo
  if (!("geolocation" in navigator)) {
     ElMessage.error("浏览器不支持定位")
     return
  }
  
  try {
     const pos = await new Promise((resolve, reject) => {
         navigator.geolocation.getCurrentPosition(resolve, reject)
     })
     
     // Store for next step
      sessionData.value = { 
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude 
      }
      currentGeo.value = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude 
      }

    const res = await axios.get(`/api/sessions/verify/${sessionCode.value}`, config)
    // Merge server data
    sessionData.value = { ...sessionData.value, ...res.data }
    
    currentStep.value = 'camera'
  } catch (err) {
    if (err.code === 1) {
        ElMessage.error("请允许获取位置信息以进行签到")
    } else {
        ElMessage.error(err.response?.data?.detail || '无效的签到码或签到已过期')
    }
  }
}

const handleLivenessSuccess = (blob) => {
  ElMessage.success('动作验证通过，正在提交...')
  submitCheckIn(blob)
}

const handleLivenessFail = (msg) => {
  ElMessage.error(msg)
  resetStep()
}

const submitCheckIn = async (blob) => {
  loading.value = true
  const formData = new FormData()
  formData.append('file', blob, 'capture.jpg')
  formData.append('session_id', sessionData.value.id)
  if (sessionData.value.latitude) {
      formData.append('latitude', sessionData.value.latitude)
      formData.append('longitude', sessionData.value.longitude)
  }
  
  try {
    await axios.post('/api/attendance/check-in', formData, config)
    ElMessage.success({
      message: '签到成功！',
      type: 'success',
      duration: 3000
    })
    resetStep()
  } catch (err) {
    if (err.response?.status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        setTimeout(() => logout(), 1500)
    } else {
        ElMessage.error('签到失败: ' + (err.response?.data?.detail || err.message))
    }
  } finally {
    loading.value = false
  }
}

const resetStep = () => {
  currentStep.value = null
  sessionCode.value = ''
}

// REMOVE OLD FUNCTIONS: startCamera, stopCamera, captureAndSign
// as they are handled by LivenessDetection component now.

const logout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  display: flex;
  flex-direction: column;
}
.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
  padding: 0 24px;
}
.header-content {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.logo {
  display: flex;
  align-items: center;
  color: #67C23A;
}
.logo h2 {
  font-size: 18px;
  margin: 0;
}
.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  padding-top: 40px;
}
.center-wrapper {
  width: 100%;
  max-width: 480px;
}
.step-card {
  width: 100%;
}
.card-header {
  text-align: center;
  margin-bottom: 20px;
}
.card-header h3 {
  margin: 0 0 8px 0;
  font-size: 22px;
  color: #303133;
}
.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.input-area {
  padding: 0 10px 20px 10px;
}

/* Camera Styles */
.camera-mode .el-card {
  overflow: hidden;
}
.camera-header {
  padding: 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  text-align: center;
}
.camera-header h3 {
  margin: 0;
  font-size: 16px;
}
.session-info {
    margin-top: 8px;
    font-size: 13px;
    color: #606266;
    display: flex;
    justify-content: center;
    gap: 15px;
}
.session-info p {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 4px;
}
.geo-info {
    margin-top: 5px;
    font-size: 12px;
    color: #409EFF;
}
.geo-info p {
    margin: 0;
}
.camera-view {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 133.33%; /* 4:3 Aspect Ratio */
  background: #000;
  overflow: hidden;
}
.camera-view video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}
.scan-frame {
  width: 60%;
  padding-bottom: 60%; /* Square */
  border: 2px solid rgba(255, 255, 255, 0.6);
  border-radius: 50%; /* Circle for face */
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.4);
  margin-bottom: 20px;
}
.overlay p {
  color: #fff;
  font-size: 16px;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
.camera-footer {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  background: #fff;
}
</style>
