import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Layout as AntLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Badge,
  theme,
} from 'antd'
import {
  DashboardOutlined,
  ApiOutlined,
  AppstoreOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../stores/auth'
import './index.less'

const { Header, Sider, Content } = AntLayout

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '概览',
  },
  {
    key: '/workflows',
    icon: <ApiOutlined />,
    label: '工作流管理',
  },
  {
    key: '/components',
    icon: <AppstoreOutlined />,
    label: '组件管理',
  },
  {
    key: '/users',
    icon: <UserOutlined />,
    label: '用户权限',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
]

export const Layout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)
  const [localUser, setLocalUser] = useState<any>(null)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  useEffect(() => {
    // 从store或localStorage获取用户信息
    if (user) {
      setLocalUser(user)
    } else {
      // 尝试从localStorage恢复用户信息
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        try {
          setLocalUser(JSON.parse(storedUser))
        } catch (e) {
          console.error('解析用户信息失败:', e)
        }
      }
    }
  }, [user])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    localStorage.removeItem('user')
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      label: '个人设置',
      icon: <UserOutlined />,
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        className="app-sider"
      >
        <div className="logo">
          {collapsed ? 'EWP' : '企业工作流平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          
          <Space size={24}>
            <Badge count={5} size="small">
              <Button type="text" icon={<BellOutlined />} />
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar src={localUser?.avatar} icon={<UserOutlined />}>
                  {localUser?.username?.[0]?.toUpperCase()}
                </Avatar>
                <span>{localUser?.full_name || localUser?.username || '用户'}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
