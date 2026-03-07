import { useState } from 'react'
import {
  Card,
  Button,
  Table,
  Input,
  Tag,
  Avatar,
  Space,
  Switch,
  message,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  UserOutlined,
  EditOutlined,
} from '@ant-design/icons'

const { Search } = Input

const mockUsers = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    full_name: '系统管理员',
    is_active: true,
    is_superuser: true,
    roles: [{ name: '管理员' }],
    department: { name: '技术部' },
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    full_name: '张三',
    is_active: true,
    is_superuser: false,
    roles: [{ name: '开发者' }],
    department: { name: '技术部' },
    created_at: '2024-01-10T10:00:00Z',
  },
  {
    id: '3',
    username: 'lisi',
    email: 'lisi@example.com',
    full_name: '李四',
    is_active: false,
    is_superuser: false,
    roles: [{ name: '普通用户' }],
    department: { name: '运营部' },
    created_at: '2024-01-15T14:30:00Z',
  },
]

export const UserListPage = () => {
  const [loading] = useState(false)
  const [searchText, setSearchText] = useState('')

  const handleToggleStatus = (userId: string, checked: boolean) => {
    message.success(`用户状态已${checked ? '启用' : '禁用'}`)
  }

  const columns = [
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: any) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{record.full_name || text}</div>
            <div style={{ fontSize: 12, color: '#666' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    { title: '用户名', dataIndex: 'username', key: 'username_text', width: 120 },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      width: 150,
      render: (roles: any[]) => (
        <Space>
          {roles.map((role, idx) => (
            <Tag key={idx} color={role.name === '管理员' ? 'red' : 'blue'}>
              {role.name}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120,
      render: (dept: any) => dept?.name || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active: boolean, record: any) => (
        <Switch
          checked={active}
          onChange={(checked) => handleToggleStatus(record.id, checked)}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: () => (
        <Button type="text" icon={<EditOutlined />}>
          编辑
        </Button>
      ),
    },
  ]

  return (
    <div className="user-list-page">
      <Card
        title="用户管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
            添加用户
          </Button>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索用户名、邮箱或姓名"
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
        </div>

        <Table
          columns={columns}
          dataSource={mockUsers}
          rowKey="id"
          loading={loading}
          pagination={{ total: mockUsers.length, pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}
