/**
 * 组件类型定义
 */

export interface Component {
  id: string;
  name: string;
  code: string;
  description?: string;
  component_type: string;
  icon?: string;
  color?: string;
  version: string;
  status: string;
  category_id?: string;
  tags: string[];
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  config_schema: Record<string, any>;
  execution_config: Record<string, any>;
  implementation?: string;
  language?: string;
  documentation?: string;
  examples: any[];
  usage_count: number;
  rating: number;
  visibility: string;
  created_by: string;
  tenant_id?: string;
  is_approved: boolean;
  created_at: string;
  updated_at?: string;
  published_at?: string;
}

export interface ComponentCategory {
  id: string;
  name: string;
  code: string;
  description?: string;
  icon?: string;
  color?: string;
  sort_order: number;
  created_at: string;
}

export interface ComponentVersion {
  id: string;
  component_id: string;
  version: string;
  changes?: string;
  implementation?: string;
  is_current: boolean;
  created_by: string;
  created_at: string;
}
