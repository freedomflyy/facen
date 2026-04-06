import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import TeacherDashboard from '../views/TeacherDashboard.vue'
import StudentDashboard from '../views/StudentDashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/teacher',
      name: 'teacher',
      component: TeacherDashboard
    },
    {
      path: '/student',
      name: 'student',
      component: StudentDashboard
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminDashboard
    }
  ]
})

export default router
