import { useState } from 'react'
import { Card, Button, Table, Tag, Space, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'

const mockRoles = [
  {
    id: '1',
    name: '管理员',
    code: 'admin',
    description: '系统管理员，拥有所有权限',
    role_type: 'system',
    user_count: 2,
  },
  {
    id: '2',
    name: '开发者',
    code: 'developer',
    description: '开发人员，可创建和编辑工作流、组件',
    role_type: 'system',
    user_count: 15,
  },
  {
    id: '3',
    name: '普通用户',
    code: 'user',
    description: '普通用户，可查看和执行工作流',
    role_type: 'system',
    user_count: 50,
  },
  {
    id: '4',
    name: '访客',
    code: 'guest',
    description: '访客，仅可查看',
    role_type: 'custom',
    user_count: 5,
  },
]

export const RoleListPage = () => {
  const [loading] = useState(false)

  const handleDelete = () => {
    message.success('角色已删除')
  }

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.description}</div>
        </div>
      ),
    },
    { title: '角色编码', dataIndex: 'code', key: 'code', width: 150 },
    {
      title: '类型',
      dataIndex: 'role_type',
      key: 'role_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'system' ? 'orange' : 'default'}>
          {type === 'system' ? '系统' : '自定义'}
        </Tag>
      ),
    },
    { title: '用户数', dataIndex: 'user_count', key: 'user_count', width: 100 },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: () => (
        <Space>
          <Button type="text" icon={<EditOutlined />}>编辑</Button>
          <Button type="text" danger icon={<DeleteOutlined />} onClick={handleDelete}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="role-list-page">
      <Card
        title="角色权限"
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
            添加角色
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={mockRoles}
          rowKey="id"
          loading={loading}
          pagination={{ total: mockRoles.length, pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}
