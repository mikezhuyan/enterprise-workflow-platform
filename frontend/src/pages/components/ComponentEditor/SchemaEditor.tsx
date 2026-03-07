import React, { useState, useEffect } from 'react'
import { Button, Input, Select, Table } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'

const { Option } = Select

interface SchemaEditorProps {
  value: any
  onChange: (val: any) => void
  title: string
}

export const SchemaEditor: React.FC<SchemaEditorProps> = ({ value, onChange, title }) => {
  const [properties, setProperties] = useState<any[]>([])
  const [required, setRequired] = useState<string[]>([])

  useEffect(() => {
    if (value) {
      const props = Object.entries(value.properties || {}).map(([key, val]: [string, any]) => ({
        key,
        ...val,
      }))
      setProperties(props)
      setRequired(value.required || [])
    }
  }, [value])

  const handleAdd = () => {
    const newProps = [...properties, { key: `param_${properties.length + 1}`, type: 'string', description: '' }]
    setProperties(newProps)
    updateValue(newProps, required)
  }

  const handleDelete = (index: number) => {
    const newProps = properties.filter((_, i) => i !== index)
    setProperties(newProps)
    updateValue(newProps, required)
  }

  const handleChange = (index: number, field: string, val: string) => {
    const newProps = [...properties]
    newProps[index][field] = val
    setProperties(newProps)
    updateValue(newProps, required)
  }

  const updateValue = (props: any[], req: string[]) => {
    const properties: Record<string, any> = {}
    props.forEach(p => {
      const { key, ...rest } = p
      properties[key] = rest
    })
    onChange({ type: 'object', properties, required: req })
  }

  return (
    <div>
      <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
        <span>{title}</span>
        <Button size="small" icon={<PlusOutlined />} onClick={handleAdd}>添加参数</Button>
      </div>
      <Table
        size="small"
        pagination={false}
        dataSource={properties.map((p, i) => ({ ...p, index: i }))}
        rowKey="index"
        columns={[
          {
            title: '参数名',
            dataIndex: 'key',
            render: (val, record) => (
              <Input
                size="small"
                value={val}
                onChange={e => handleChange(record.index, 'key', e.target.value)}
              />
            )
          },
          {
            title: '类型',
            dataIndex: 'type',
            render: (val, record) => (
              <Select
                size="small"
                value={val}
                onChange={v => handleChange(record.index, 'type', v)}
                style={{ width: 100 }}
              >
                <Option value="string">字符串</Option>
                <Option value="number">数字</Option>
                <Option value="boolean">布尔</Option>
                <Option value="object">对象</Option>
                <Option value="array">数组</Option>
              </Select>
            )
          },
          {
            title: '描述',
            dataIndex: 'description',
            render: (val, record) => (
              <Input
                size="small"
                value={val}
                onChange={e => handleChange(record.index, 'description', e.target.value)}
                placeholder="参数描述"
              />
            )
          },
          {
            title: '操作',
            width: 60,
            render: (_, record) => (
              <Button
                size="small"
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record.index)}
              />
            )
          }
        ]}
      />
    </div>
  )
}

export default SchemaEditor
