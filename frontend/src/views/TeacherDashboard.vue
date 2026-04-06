<template>
  <div class="dashboard-container">
    <el-header class="header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="24" style="margin-right: 8px"><Monitor /></el-icon>
          <h2>教师管理工作台</h2>
        </div>
        <div class="user-info">
          <span>欢迎您，{{ username }}</span>
          <el-button type="danger" plain size="small" @click="logout" style="margin-left: 15px">退出登录</el-button>
        </div>
      </div>
    </el-header>
    
    <el-main class="main-content">
      <el-row :gutter="24">
        <!-- 左侧：功能区 -->
        <el-col :span="10">
          <!-- 创建签到 -->
          <el-card class="box-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><CirclePlus /></el-icon>
                <span>发布新签到</span>
              </div>
            </template>
            <el-form :model="sessionForm" label-position="top">
              <el-form-item label="课程名称">
                <el-input v-model="sessionForm.name" placeholder="例如：高等数学 第3节" />
              </el-form-item>
              <el-form-item label="目标班级 (可多选)">
                <el-select v-model="sessionForm.target_classes" multiple placeholder="请选择上课班级" style="width: 100%">
                   <el-option 
                    v-for="c in classList" 
                    :key="c.id" 
                    :label="c.name" 
                    :value="c.id" 
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="位置限制">
                <el-checkbox v-model="sessionForm.enable_geo">仅限当前位置附近 (100米)</el-checkbox>
              </el-form-item>
              <el-form-item label="有效时长 (分钟)">
                <el-input-number v-model="sessionForm.duration" :min="1" :max="120" style="width: 100%" />
              </el-form-item>
              <el-button type="primary" @click="createSession" style="width: 100%" size="large">立即发布</el-button>
            </el-form>
          </el-card>

          <!-- 人数统计 -->
          <el-card class="box-card" shadow="hover" style="margin-top: 24px;">
             <template #header>
              <div class="card-header">
                <el-icon><Camera /></el-icon>
                <span>课堂人数统计 (模拟)</span>
              </div>
            </template>
            <div class="upload-area">
              <el-upload
                class="upload-demo"
                action="/api/count-faces"
                :on-success="handleCountSuccess"
                :show-file-list="false"
                name="file"
                drag
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽图片到此处或 <em>点击上传</em>
                </div>
              </el-upload>
            </div>
            <div v-if="headcount !== null" class="count-result">
              <span class="label">检测人数：</span>
              <span class="number">{{ headcount }}</span>
              <span class="unit">人</span>
              <div v-if="countImage" style="margin-top: 10px;">
                  <el-image 
                    :src="countImage" 
                    :preview-src-list="[countImage]"
                    fit="contain"
                    style="max-height: 200px; width: 100%; border-radius: 4px;"
                  />
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：列表区 -->
        <el-col :span="14">
          <el-card class="box-card" shadow="hover" style="height: 100%">
            <template #header>
              <div class="card-header">
                <div style="display: flex; align-items: center;">
                  <el-icon><List /></el-icon>
                  <span>历史签到记录</span>
                </div>
                <el-button circle size="small" @click="fetchSessions">
                   <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <el-table :data="sessions" style="width: 100%" stripe>
              <el-table-column prop="name" label="课程名称" />
              <el-table-column prop="code" label="签到码" width="100">
                 <template #default="scope">
                   <el-tag effect="dark" type="success">{{ scope.row.code }}</el-tag>
                 </template>
              </el-table-column>
              <el-table-column label="位置/时长" width="180">
                <template #default="scope">
                   <div v-if="scope.row.latitude" style="font-size: 12px; line-height: 1.4;">
                     <div><el-icon><Location /></el-icon> {{ scope.row.latitude.toFixed(4) }}, {{ scope.row.longitude.toFixed(4) }}</div>
                     <div><el-icon><Clock /></el-icon> {{ Math.round((new Date(scope.row.end_time) - new Date(scope.row.start_time))/60000) }} 分钟</div>
                   </div>
                   <div v-else>
                     <el-tag size="small" type="info">无位置限制</el-tag>
                     <div style="font-size: 12px; margin-top: 4px;"><el-icon><Clock /></el-icon> {{ Math.round((new Date(scope.row.end_time) - new Date(scope.row.start_time))/60000) }} 分钟</div>
                   </div>
                </template>
              </el-table-column>
              <el-table-column label="发布时间" width="160">
                <template #default="scope">
                  {{ new Date(scope.row.start_time).toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="right">
                <template #default="scope">
                  <el-button size="small" type="primary" plain @click="viewAttendance(scope.row.id)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 签到详情弹窗 -->
      <el-dialog v-model="dialogVisible" title="签到详情列表" width="800px">
        <el-tabs type="card">
          <el-tab-pane label="已签到名单">
            <el-table :data="attendanceRecords.filter(r => r.status.includes('checked_in'))" border height="400">
              <el-table-column prop="student_name" label="姓名" width="100" />
              <el-table-column prop="student_id" label="学号" width="120" />
              <el-table-column prop="class_name" label="班级" width="120" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag type="success">
                    {{ scope.row.status === 'checked_in_manual' ? '手动' : '正常' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="check_in_time" label="签到时间" />
            </el-table>
          </el-tab-pane>
          
          <el-tab-pane label="缺勤/未到名单">
             <el-table :data="attendanceRecords.filter(r => r.status === 'absent')" border height="400">
              <el-table-column prop="student_name" label="姓名" width="100" />
              <el-table-column prop="student_id" label="学号" width="120" />
              <el-table-column prop="class_name" label="班级" width="120" />
              <el-table-column label="操作" align="center">
                <template #default="scope">
                  <el-button size="small" type="warning" @click="manualCheckIn(scope.row)">
                    手动补签
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-dialog>
    </el-main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, CirclePlus, Camera, List, Refresh, UploadFilled, Location, Clock } from '@element-plus/icons-vue'

const router = useRouter()
const sessionForm = ref({ 
  name: '', 
  duration: 30,
  target_classes: [],
  enable_geo: false,
  latitude: null,
  longitude: null
})

const classList = ref([])

const sessions = ref([])
const headcount = ref(null)
const countImage = ref(null)
const dialogVisible = ref(false)
const attendanceRecords = ref([])
const currentSessionId = ref(null)
const username = ref('')

const token = localStorage.getItem('token')
const config = { headers: { Authorization: `Bearer ${token}` } }

onMounted(async () => {
  username.value = localStorage.getItem('username') || '教师'
  fetchSessions()
  
  // Fetch classes (assigned only)
  try {
      const res = await axios.get('/api/teachers/me/classes', config)
      classList.value = res.data
  } catch(e) { console.error(e) }
})

const fetchSessions = async () => {
  try {
    const res = await axios.get('/api/sessions', config)
    sessions.value = res.data
  } catch (err) {
    if(err.response?.status === 401) router.push('/login')
    ElMessage.error('获取列表失败')
  }
}

const createSession = async () => {
  if(!sessionForm.value.name) {
    ElMessage.warning('请输入课程名称')
    return
  }
  
  // Get Geo if enabled
  if (sessionForm.value.enable_geo) {
     if (!("geolocation" in navigator)) {
       ElMessage.error("浏览器不支持定位")
       return
     }
     try {
       const pos = await new Promise((resolve, reject) => {
         navigator.geolocation.getCurrentPosition(resolve, reject)
       })
       sessionForm.value.latitude = pos.coords.latitude
       sessionForm.value.longitude = pos.coords.longitude
     } catch (e) {
       ElMessage.error("无法获取位置信息，请检查权限")
       return
     }
  } else {
     sessionForm.value.latitude = null
     sessionForm.value.longitude = null
  }

  try {
    const payload = { ...sessionForm.value }
    // Convert array to comma separated string if backend expects string, 
    // BUT we updated backend model to store string, so frontend should join it.
    // However, if we want to send it as JSON array, backend needs to parse it.
    // Let's check backend... backend expects session_data dict.
    // We will join it here for simplicity to match the DB model directly, 
    // OR update backend to handle list. 
    // Let's update backend to handle list -> string conversion.
    // Actually, sending as list is cleaner for API, let backend convert.
    // Wait, axios sends JSON.
    
    await axios.post('/api/sessions', payload, config)
    ElMessage.success('签到发布成功')
    sessionForm.value.name = ''
    sessionForm.value.target_classes = []
    fetchSessions()
  } catch (err) {
    ElMessage.error('创建失败')
  }
}

const handleCountSuccess = (response) => {
  headcount.value = response.count
  countImage.value = response.image_base64
  ElMessage.success(`识别完成：共 ${response.count} 人`)
}

const viewAttendance = async (sessionId) => {
  currentSessionId.value = sessionId
  try {
    const res = await axios.get(`/api/sessions/${sessionId}/attendance`, config)
    attendanceRecords.value = res.data
    dialogVisible.value = true
  } catch (err) {
    ElMessage.error('获取详情失败')
  }
}

const manualCheckIn = async (row) => {
    try {
        await axios.post('/api/attendance/manual-check-in', {
            session_id: currentSessionId.value,
            student_id: row.student_user_id
        }, config)
        ElMessage.success(`已为 ${row.student_name} 补签`)
        viewAttendance(currentSessionId.value) // 刷新列表
    } catch (e) {
        ElMessage.error("补签失败")
    }
}

const logout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}
.header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
}
.header-content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.logo {
  display: flex;
  align-items: center;
  color: #409EFF;
}
.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.main-content {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 20px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.upload-area {
  text-align: center;
}
.count-result {
  margin-top: 16px;
  text-align: center;
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  color: #67c23a;
}
.count-result .number {
  font-size: 28px;
  font-weight: bold;
  margin: 0 4px;
}
</style>
