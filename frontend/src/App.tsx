import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuthStore } from './stores/auth'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/Login'
import { DashboardPage } from './pages/Dashboard'
import { WorkflowListPage } from './pages/workflows/WorkflowList'
import { WorkflowEditorPage } from './pages/workflows/WorkflowEditor'
import { ComponentListPage } from './pages/components/ComponentList'
import { ComponentEditorPage } from './pages/components/ComponentEditor'
import { UserListPage } from './pages/users/UserList'
import { RoleListPage } from './pages/users/RoleList'
import { SettingsPage } from './pages/settings/Settings'
import './App.less'

// 路由守卫组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isChecking, setIsChecking] = useState(true)
  const [isAuth, setIsAuth] = useState(false)
  
  useEffect(() => {
    const token = localStorage.getItem('token')
    setIsAuth(!!token)
    setIsChecking(false)
  }, [])
  
  if (isChecking) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>加载中...</div>
  }
  
  if (!isAuth) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  const { initialize } = useAuthStore()
  
  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="workflows">
          <Route index element={<WorkflowListPage />} />
          <Route path="new" element={<WorkflowEditorPage />} />
          <Route path=":id" element={<WorkflowEditorPage />} />
        </Route>
        <Route path="components">
          <Route index element={<ComponentListPage />} />
          <Route path="new" element={<ComponentEditorPage />} />
          <Route path=":id" element={<ComponentEditorPage />} />
        </Route>
        <Route path="users">
          <Route index element={<UserListPage />} />
          <Route path="roles" element={<RoleListPage />} />
        </Route>
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
