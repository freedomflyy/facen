<template>
  <div class="admin-container">
    <el-container>
      <el-aside width="220px" class="aside">
        <div class="logo">
          <h2>系统管理后台</h2>
        </div>
        <el-menu :default-active="activeMenu" class="el-menu-vertical" @select="handleSelect">
          <el-menu-item index="stats">
            <el-icon><DataLine /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          <el-menu-item index="teachers">
            <el-icon><User /></el-icon>
            <span>教师管理</span>
          </el-menu-item>
          <el-menu-item index="students">
            <el-icon><UserFilled /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
          <el-menu-item index="classes">
            <el-icon><School /></el-icon>
            <span>班级管理</span>
          </el-menu-item>
          <el-menu-item index="sessions">
            <el-icon><List /></el-icon>
            <span>签到管理</span>
          </el-menu-item>
        </el-menu>
        <div class="logout-btn">
             <el-button type="danger" plain @click="logout" style="width: 100%">退出登录</el-button>
        </div>
      </el-aside>
      
      <el-main class="main-content">
        <!-- Stats -->
        <div v-if="activeMenu === 'stats'">
            <h2 class="page-title">系统数据概览</h2>
            <el-row :gutter="20">
                <el-col :span="6">
                    <el-card shadow="hover" class="stat-card">
                        <h3>学生总数</h3>
                        <div class="stat-num">{{ stats.students }}</div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card shadow="hover" class="stat-card">
                        <h3>教师总数</h3>
                        <div class="stat-num">{{ stats.teachers }}</div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card shadow="hover" class="stat-card">
                        <h3>班级总数</h3>
                        <div class="stat-num">{{ stats.classes }}</div>
                    </el-card>
                </el-col>
                <el-col :span="6">
                    <el-card shadow="hover" class="stat-card">
                        <h3>总签到场次</h3>
                        <div class="stat-num">{{ stats.sessions }}</div>
                    </el-card>
                </el-col>
            </el-row>
        </div>

        <!-- Teacher Management -->
        <div v-if="activeMenu === 'teachers'">
            <div class="header-actions">
                <h2 class="page-title">教师列表</h2>
                <div style="display: flex; gap: 10px;">
                    <el-input v-model="teacherSearch" placeholder="搜索姓名/用户名" style="width: 200px;" clearable />
                    <el-button type="primary" @click="showAddTeacher = true">新增教师</el-button>
                </div>
            </div>
            <el-table :data="filteredTeachers" stripe border>
                <el-table-column prop="username" label="用户名" />
                <el-table-column prop="full_name" label="姓名" />
                <el-table-column label="操作" width="220">
                    <template #default="scope">
                        <el-button size="small" type="primary" plain @click="openAssign(scope.row)">分配班级</el-button>
                        <el-button size="small" link @click="openEditTeacher(scope.row)">编辑</el-button>
                        <el-popconfirm title="确定删除该教师吗?" @confirm="deleteTeacher(scope.row)">
                             <template #reference>
                                 <el-button size="small" type="danger" link>删除</el-button>
                             </template>
                        </el-popconfirm>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <!-- Student Management -->
        <div v-if="activeMenu === 'students'">
            <div class="header-actions">
                <h2 class="page-title">学生列表</h2>
                <div style="display: flex; gap: 10px;">
                     <el-input v-model="studentSearch" placeholder="搜索姓名/学号" style="width: 200px;" clearable />
                     <el-select v-model="studentClassFilter" placeholder="按班级筛选" clearable style="width: 150px;">
                        <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.name" />
                     </el-select>
                     <el-button type="primary" @click="showAddStudent = true">新增学生</el-button>
                </div>
            </div>
            <el-table :data="filteredStudents" stripe border height="calc(100vh - 140px)">
                <el-table-column prop="student_id" label="学号" width="120" sortable />
                <el-table-column prop="full_name" label="姓名" width="120" />
                <el-table-column prop="username" label="账号" width="120" />
                <el-table-column prop="class_name" label="班级" width="120" sortable />
                <el-table-column prop="major" label="专业" />
                <el-table-column label="操作" width="150" fixed="right">
                    <template #default="scope">
                        <el-button type="primary" link size="small" @click="openEditStudent(scope.row)">编辑</el-button>
                        <el-popconfirm title="确定删除该学生吗?" @confirm="deleteStudent(scope.row)">
                            <template #reference>
                                <el-button type="danger" link size="small">删除</el-button>
                            </template>
                        </el-popconfirm>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <!-- Class Management -->
        <div v-if="activeMenu === 'classes'">
             <div class="header-actions">
                <h2 class="page-title">班级列表</h2>
                <div style="display: flex; gap: 10px;">
                    <el-input v-model="classSearch" placeholder="搜索班级/专业" style="width: 200px;" clearable />
                    <el-button type="primary" @click="showAddClass = true">新增班级</el-button>
                </div>
            </div>
            <el-table :data="filteredClasses" stripe border>
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="name" label="班级名称" />
                <el-table-column prop="major" label="所属专业" />
                <el-table-column label="操作" width="150">
                    <template #default="scope">
                        <el-button size="small" link @click="openEditClass(scope.row)">编辑</el-button>
                        <el-popconfirm title="确定删除该班级吗? (需无关联学生)" @confirm="deleteClass(scope.row)">
                             <template #reference>
                                 <el-button size="small" type="danger" link>删除</el-button>
                             </template>
                        </el-popconfirm>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <!-- Session Management -->
        <div v-if="activeMenu === 'sessions'">
            <h2 class="page-title">全校签到场次</h2>
            <el-table :data="sessions" stripe border>
                <el-table-column prop="name" label="课程名称" />
                <el-table-column prop="code" label="签到码" width="100">
                    <template #default="scope">
                        <el-tag effect="dark" type="success">{{ scope.row.code }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="creator_name" label="发起教师" width="120" />
                <el-table-column label="发起时间" width="180">
                    <template #default="scope">
                        {{ new Date(scope.row.start_time).toLocaleString() }}
                    </template>
                </el-table-column>
                <el-table-column label="签到人数" width="100">
                    <template #default="scope">
                        <el-tag>{{ scope.row.attendance_count }} 人</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="180">
                    <template #default="scope">
                        <el-button size="small" @click="viewSessionDetail(scope.row)">详情</el-button>
                        <el-popconfirm title="确定删除该签到记录吗?" @confirm="deleteSession(scope.row.id)">
                            <template #reference>
                                <el-button size="small" type="danger" plain>删除</el-button>
                            </template>
                        </el-popconfirm>
                    </template>
                </el-table-column>
            </el-table>
        </div>
      </el-main>
    </el-container>

    <!-- Dialogs -->
    <el-dialog v-model="showStudents" :title="currentClassName + ' 学生名单'" width="600px">
         <el-table :data="currentClassStudents" border height="400">
             <el-table-column prop="student_id" label="学号" width="120" />
             <el-table-column prop="full_name" label="姓名" width="120" />
             <el-table-column prop="username" label="账号" />
             <el-table-column label="操作" width="150">
                <template #default="scope">
                    <el-button type="primary" link size="small" @click="openEditStudent(scope.row)">编辑</el-button>
                    <el-popconfirm title="确定删除该学生吗?" @confirm="deleteStudent(scope.row)">
                        <template #reference>
                            <el-button type="danger" link size="small">删除</el-button>
                        </template>
                    </el-popconfirm>
                </template>
             </el-table-column>
         </el-table>
    </el-dialog>

    <el-dialog v-model="showAddStudent" title="新增学生" width="400px">
        <el-form :model="newStudentForm" label-width="80px">
            <el-form-item label="用户名">
                <el-input v-model="newStudentForm.username" />
            </el-form-item>
            <el-form-item label="密码">
                <el-input v-model="newStudentForm.password" type="password" show-password />
            </el-form-item>
            <el-form-item label="姓名">
                <el-input v-model="newStudentForm.full_name" />
            </el-form-item>
            <el-form-item label="学号">
                <el-input v-model="newStudentForm.student_id" />
            </el-form-item>
            <el-form-item label="班级">
                 <el-select v-model="newStudentForm.class_id" placeholder="选择班级" style="width: 100%">
                    <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
                 </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showAddStudent = false">取消</el-button>
            <el-button type="primary" @click="createStudent">确认</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showEditStudent" title="编辑学生信息" width="400px">
        <el-form :model="studentForm" label-width="80px">
            <el-form-item label="姓名">
                <el-input v-model="studentForm.full_name" />
            </el-form-item>
            <el-form-item label="学号">
                <el-input v-model="studentForm.student_id" />
            </el-form-item>
            <el-form-item label="班级">
                 <el-select v-model="studentForm.class_id" placeholder="选择班级" style="width: 100%">
                    <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
                 </el-select>
            </el-form-item>
            <el-form-item label="重置密码">
                <el-input v-model="studentForm.password" placeholder="不修改请留空" show-password />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showEditStudent = false">取消</el-button>
            <el-button type="primary" @click="updateStudent">保存</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showSessionDetail" title="签到详情与管理" width="800px">
         <el-table :data="sessionAttendance" border height="500">
             <el-table-column prop="student_name" label="姓名" width="120" />
             <el-table-column prop="student_id" label="学号" width="120" />
             <el-table-column prop="class_name" label="班级" width="120" />
             <el-table-column prop="status" label="状态" width="120">
                 <template #default="scope">
                     <el-tag :type="getStatusType(scope.row.status)">{{ getStatusLabel(scope.row.status) }}</el-tag>
                 </template>
             </el-table-column>
             <el-table-column label="管理操作">
                 <template #default="scope">
                     <el-select 
                        v-model="scope.row.status" 
                        size="small" 
                        style="width: 110px"
                        @change="(val) => updateAttendance(scope.row, val)"
                     >
                         <el-option label="已签到" value="checked_in" />
                         <el-option label="迟到" value="late" />
                         <el-option label="缺勤" value="absent" />
                         <el-option label="请假" value="leave" />
                     </el-select>
                 </template>
             </el-table-column>
         </el-table>
    </el-dialog>

    <el-dialog v-model="showAddTeacher" title="新增教师" width="400px">
        <el-form :model="teacherForm">
            <el-form-item label="用户名">
                <el-input v-model="teacherForm.username" />
            </el-form-item>
            <el-form-item label="密码">
                <el-input v-model="teacherForm.password" type="password" show-password />
            </el-form-item>
            <el-form-item label="姓名">
                <el-input v-model="teacherForm.full_name" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showAddTeacher = false">取消</el-button>
            <el-button type="primary" @click="createTeacher">确认</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showAddClass" title="新增班级" width="400px">
        <el-form :model="classForm">
            <el-form-item label="班级名称">
                <el-input v-model="classForm.name" placeholder="如: 计科2101" />
            </el-form-item>
            <el-form-item label="专业">
                <el-input v-model="classForm.major" placeholder="如: 计算机科学与技术" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showAddClass = false">取消</el-button>
            <el-button type="primary" @click="createClass">确认</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showEditTeacher" title="编辑教师信息" width="400px">
        <el-form :model="teacherEditForm" label-width="80px">
            <el-form-item label="姓名">
                <el-input v-model="teacherEditForm.full_name" />
            </el-form-item>
            <el-form-item label="重置密码">
                <el-input v-model="teacherEditForm.password" placeholder="不修改请留空" show-password />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showEditTeacher = false">取消</el-button>
            <el-button type="primary" @click="updateTeacher">保存</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showEditClass" title="编辑班级信息" width="400px">
        <el-form :model="classEditForm" label-width="80px">
            <el-form-item label="班级名称">
                <el-input v-model="classEditForm.name" />
            </el-form-item>
            <el-form-item label="专业">
                <el-input v-model="classEditForm.major" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="showEditClass = false">取消</el-button>
            <el-button type="primary" @click="updateClass">保存</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="showAssign" title="分配负责班级" width="500px">
        <p>正在为 <b>{{ currentTeacher?.full_name }}</b> 分配班级：</p>
        <el-transfer 
            v-model="assignedClasses" 
            :data="classTransferData" 
            :titles="['可选班级', '已分配']"
        />
        <template #footer>
            <el-button @click="showAssign = false">取消</el-button>
            <el-button type="primary" @click="confirmAssign">保存设置</el-button>
        </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataLine, User, School, List, UserFilled } from '@element-plus/icons-vue'

const router = useRouter()
const activeMenu = ref('stats')
const stats = ref({})
const teachers = ref([])
const classes = ref([])
const students = ref([]) // All students
const sessions = ref([])

const showAddTeacher = ref(false)
const teacherForm = ref({ username: '', password: '', full_name: '' })

const showAddStudent = ref(false) // New Student
const newStudentForm = ref({ username: '', password: '', full_name: '', student_id: '', class_id: null })

const showAddClass = ref(false)
const classForm = ref({ name: '', major: '' })

const showAssign = ref(false)
const currentTeacher = ref(null)
const assignedClasses = ref([])

const showEditStudent = ref(false)
const studentForm = ref({ id: null, full_name: '', student_id: '', password: '', class_id: null })

const showEditTeacher = ref(false)
const teacherEditForm = ref({ id: null, full_name: '', password: '' })

const showEditClass = ref(false)
const classEditForm = ref({ id: null, name: '', major: '' })

// Filters
const teacherSearch = ref('')
const classSearch = ref('')

// Filters for student list
const studentSearch = ref('')
const studentClassFilter = ref('')

const showSessionDetail = ref(false)
const currentSession = ref(null)
const sessionAttendance = ref([])

const token = localStorage.getItem('token')
const config = { headers: { Authorization: `Bearer ${token}` } }

onMounted(() => {
    fetchStats()
    fetchTeachers()
    fetchClasses()
    fetchStudents() // New
    fetchSessions()
})

// ...

const fetchStudents = async () => {
    try {
        const res = await axios.get('/api/admin/students', config)
        students.value = res.data
    } catch(e) { console.error(e) }
}

const filteredStudents = computed(() => {
    let res = students.value
    if (studentClassFilter.value) {
        res = res.filter(s => s.class_name === studentClassFilter.value)
    }
    if (studentSearch.value) {
        const key = studentSearch.value.toLowerCase()
        res = res.filter(s => 
            (s.full_name && s.full_name.toLowerCase().includes(key)) || 
            (s.student_id && s.student_id.toLowerCase().includes(key))
        )
    }
    return res
})

const createStudent = async () => {
    try {
        await axios.post('/api/admin/students', newStudentForm.value, config)
        ElMessage.success("创建成功")
        showAddStudent.value = false
        newStudentForm.value = { username: '', password: '', full_name: '', student_id: '', class_id: null }
        fetchStudents()
        fetchStats()
    } catch (e) {
        ElMessage.error("创建失败: " + e.response?.data?.detail)
    }
}

const updateStudent = async () => {
    try {
        await axios.put(`/api/admin/users/${studentForm.value.id}`, studentForm.value, config)
        ElMessage.success("修改成功")
        showEditStudent.value = false
        fetchStudents()
    } catch (e) {
        ElMessage.error("修改失败")
    }
}

const deleteStudent = async (student) => {
    try {
        await axios.delete(`/api/admin/users/${student.id}`, config)
        ElMessage.success("删除成功")
        fetchStudents()
        fetchStats()
    } catch (e) {
        ElMessage.error("删除失败")
    }
}

const handleSelect = (key) => activeMenu.value = key

const fetchStats = async () => {
    try {
        const res = await axios.get('/api/admin/stats', config)
        stats.value = res.data
    } catch (e) {
        if(e.response?.status === 403) router.push('/login')
    }
}

const fetchTeachers = async () => {
    const res = await axios.get('/api/admin/teachers', config)
    teachers.value = res.data
}

const fetchClasses = async () => {
    const res = await axios.get('/api/classes', config)
    classes.value = res.data
}

const fetchSessions = async () => {
    const res = await axios.get('/api/admin/sessions', config)
    sessions.value = res.data
}

const filteredTeachers = computed(() => {
    let res = teachers.value
    if (teacherSearch.value) {
        const key = teacherSearch.value.toLowerCase()
        res = res.filter(t => 
            (t.full_name && t.full_name.toLowerCase().includes(key)) || 
            (t.username && t.username.toLowerCase().includes(key))
        )
    }
    return res
})

const filteredClasses = computed(() => {
    let res = classes.value
    if (classSearch.value) {
        const key = classSearch.value.toLowerCase()
        res = res.filter(c => 
            (c.name && c.name.toLowerCase().includes(key)) || 
            (c.major && c.major.toLowerCase().includes(key))
        )
    }
    return res
})

const openEditTeacher = (teacher) => {
    teacherEditForm.value = { ...teacher, password: '' }
    showEditTeacher.value = true
}

const updateTeacher = async () => {
    try {
        await axios.put(`/api/admin/users/${teacherEditForm.value.id}`, teacherEditForm.value, config)
        ElMessage.success("修改成功")
        showEditTeacher.value = false
        fetchTeachers()
    } catch (e) {
        ElMessage.error("修改失败")
    }
}

const deleteTeacher = async (teacher) => {
    try {
        await axios.delete(`/api/admin/users/${teacher.id}`, config)
        ElMessage.success("删除成功")
        fetchTeachers()
        fetchStats()
    } catch (e) {
        ElMessage.error("删除失败")
    }
}

const openEditClass = (cls) => {
    classEditForm.value = { ...cls }
    showEditClass.value = true
}

const updateClass = async () => {
    try {
        await axios.put(`/api/admin/classes/${classEditForm.value.id}`, classEditForm.value, config)
        ElMessage.success("修改成功")
        showEditClass.value = false
        fetchClasses()
    } catch (e) {
        ElMessage.error("修改失败")
    }
}

const deleteClass = async (cls) => {
    try {
        await axios.delete(`/api/admin/classes/${cls.id}`, config)
        ElMessage.success("删除成功")
        fetchClasses()
        fetchStats()
    } catch (e) {
        ElMessage.error("删除失败: " + e.response?.data?.detail)
    }
}

const createTeacher = async () => {
    try {
        await axios.post('/api/admin/teachers', teacherForm.value, config)
        ElMessage.success("教师创建成功")
        showAddTeacher.value = false
        fetchTeachers()
    } catch (e) {
        ElMessage.error("创建失败: " + e.response?.data?.detail)
    }
}

const createClass = async () => {
    try {
        await axios.post('/api/admin/classes', classForm.value, config)
        ElMessage.success("班级创建成功")
        showAddClass.value = false
        fetchClasses()
    } catch (e) {
        ElMessage.error("创建失败")
    }
}

// Assignment Logic
const classTransferData = computed(() => {
    return classes.value.map(c => ({
        key: c.id,
        label: c.name,
        disabled: false
    }))
})

const openAssign = async (teacher) => {
    currentTeacher.value = teacher
    try {
        const res = await axios.get(`/api/admin/teachers/${teacher.id}/classes`, config)
        assignedClasses.value = res.data
        showAssign.value = true
    } catch (e) {
        ElMessage.error("获取分配信息失败")
    }
}

const confirmAssign = async () => {
    try {
        await axios.post(`/api/admin/teachers/${currentTeacher.value.id}/assign`, assignedClasses.value, config)
        ElMessage.success("分配成功")
        showAssign.value = false
    } catch (e) {
        ElMessage.error("分配失败")
    }
}

const viewStudents = async (cls) => {
    currentClassName.value = cls.name
    try {
        const res = await axios.get(`/api/admin/classes/${cls.id}/students`, config)
        currentClassStudents.value = res.data
        showStudents.value = true
    } catch(e) {
        ElMessage.error("获取学生列表失败")
    }
}

const openEditStudent = (student) => {
    studentForm.value = { ...student, password: '' }
    showEditStudent.value = true
}

// REMOVE DUPLICATE FUNCTIONS BELOW (updateStudent, deleteStudent) as they are redefined above
const viewSessionDetail = async (session) => {
    currentSession.value = session
    try {
        const res = await axios.get(`/api/admin/sessions/${session.id}/attendance`, config)
        sessionAttendance.value = res.data
        showSessionDetail.value = true
    } catch (e) {
        ElMessage.error("获取详情失败")
    }
}

const updateAttendance = async (row, newStatus) => {
    try {
        if (row.id) {
            // Update existing
            await axios.put(`/api/admin/attendance/${row.id}`, { status: newStatus }, config)
        } else {
            // Create manual record for absent student
             await axios.post(`/api/admin/sessions/${currentSession.value.id}/attendance`, { 
                 student_id: row.student_user_id,
                 status: newStatus
             }, config)
             // Refresh to get ID
             viewSessionDetail(currentSession.value)
        }
        ElMessage.success("状态更新成功")
    } catch (e) {
        ElMessage.error("更新失败")
    }
}

const getStatusType = (status) => {
    const map = { checked_in: 'success', late: 'warning', absent: 'danger', leave: 'info' }
    return map[status] || 'info'
}

const getStatusLabel = (status) => {
    const map = { checked_in: '已签到', late: '迟到', absent: '缺勤', leave: '请假' }
    return map[status] || status
}

const deleteSession = async (sessionId) => {
    try {
        await axios.delete(`/api/admin/sessions/${sessionId}`, config)
        ElMessage.success("删除成功")
        fetchSessions()
        fetchStats() // Refresh stats too
    } catch(e) {
        ElMessage.error("删除失败")
    }
}

const logout = () => {
    localStorage.clear()
    router.push('/login')
}
</script>

<style scoped>
.admin-container {
    height: 100vh;
    display: flex;
}
.aside {
    background-color: #304156;
    color: #fff;
    display: flex;
    flex-direction: column;
}
.logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #2b3649;
}
.logo h2 {
    color: #fff;
    font-size: 18px;
    margin: 0;
}
.el-menu-vertical {
    border-right: none;
    flex: 1;
}
:deep(.el-menu) {
    background-color: #304156;
}
:deep(.el-menu-item) {
    color: #bfcbd9;
}
:deep(.el-menu-item:hover), :deep(.el-menu-item.is-active) {
    background-color: #263445;
    color: #409EFF;
}
.logout-btn {
    padding: 20px;
}
.main-content {
    background: #f0f2f5;
    padding: 20px;
}
.page-title {
    margin-top: 0;
    margin-bottom: 20px;
    color: #303133;
}
.stat-card {
    text-align: center;
}
.stat-card h3 {
    margin: 0 0 10px;
    color: #909399;
    font-size: 14px;
}
.stat-num {
    font-size: 28px;
    font-weight: bold;
    color: #303133;
}
.header-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
</style>
