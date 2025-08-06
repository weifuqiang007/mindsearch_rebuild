# 环境配置管理指南

## 概述

本项目支持多环境配置管理，可以根据不同的运行环境自动选择相应的配置文件。

## 配置文件说明

### 开发环境配置
- **文件名**: `.dev_env`
- **用途**: 开发环境专用配置
- **特点**: 包含开发环境的数据库、Redis等服务配置

### 生产环境配置
- **文件名**: `.env`
- **用途**: 生产环境配置
- **特点**: 包含生产环境的安全配置

### 配置模板
- **文件名**: `.env.example`
- **用途**: 配置文件模板，包含所有必需的配置项

## 环境切换方法

### 方法1: 设置环境变量

```bash
# 开发环境（默认）
export ENVIRONMENT=development
python test_config.py

# 生产环境
export ENVIRONMENT=production
python test_config.py
```

### 方法2: 临时设置

```bash
# 开发环境
ENVIRONMENT=development python test_config.py

# 生产环境
ENVIRONMENT=production python test_config.py
```

## 配置加载机制

1. **环境检测**: 通过 `ENVIRONMENT` 环境变量确定当前环境
2. **文件选择**: 
   - `development` → `.dev_env`
   - `production` → `.env`
   - 其他/未设置 → `.env`（默认）
3. **单次加载**: 使用 `CONFIG_LOADED` 标志避免重复加载
4. **配置应用**: 所有配置类使用统一的环境文件

## 最佳实践

### 开发环境设置

1. 复制配置模板：
```bash
cp .env.example .dev_env
```

2. 编辑开发配置：
```bash
# .dev_env
ENVIRONMENT=development
DEFAULT_LLM_PROVIDER=siliconflow
POSTGRES_HOST=192.168.0.141
REDIS_HOST=192.168.0.141
# ... 其他开发环境配置
```

3. 设置环境变量：
```bash
export ENVIRONMENT=development
```

### 生产环境设置

1. 创建生产配置：
```bash
cp .env.example .env
```

2. 编辑生产配置：
```bash
# .env
ENVIRONMENT=production
DEFAULT_LLM_PROVIDER=openai
POSTGRES_HOST=prod-db-server
REDIS_HOST=prod-redis-server
# ... 其他生产环境配置
```

3. 设置环境变量：
```bash
export ENVIRONMENT=production
```

## 配置验证

运行测试脚本验证配置：

```bash
# 测试开发环境配置
ENVIRONMENT=development python test_config.py

# 测试生产环境配置
ENVIRONMENT=production python test_config.py
```

## 安全注意事项

1. **敏感信息**: 生产环境的 `.env` 文件不应提交到版本控制
2. **权限控制**: 确保配置文件具有适当的文件权限
3. **密钥管理**: 生产环境建议使用密钥管理服务
4. **环境隔离**: 开发和生产环境应使用不同的数据库和服务

## 故障排除

### 常见问题

1. **配置文件不存在**
   - 确保 `.dev_env` 或 `.env` 文件存在
   - 检查文件路径和权限

2. **环境变量未生效**
   - 确认 `ENVIRONMENT` 环境变量设置正确
   - 重启终端或重新加载环境变量

3. **配置重复加载**
   - 检查 `CONFIG_LOADED` 环境变量
   - 必要时清除：`unset CONFIG_LOADED`

### 调试命令

```bash
# 查看当前环境设置
echo $ENVIRONMENT

# 查看配置加载状态
echo $CONFIG_LOADED

# 清除配置加载标志
unset CONFIG_LOADED
```

## 示例输出

### 开发环境
```
🔧 使用开发环境配置: .dev_env
✅ 环境变量已从 .dev_env 加载
📋 当前环境变量 (来自 .dev_env):
DEFAULT_LLM_PROVIDER: siliconflow
POSTGRES_HOST: 192.168.0.141
...
🎯 测试完成！当前使用环境: development (.dev_env)
```

### 生产环境
```
🚀 使用生产环境配置: .env
✅ 环境变量已从 .env 加载
📋 当前环境变量 (来自 .env):
DEFAULT_LLM_PROVIDER: openai
POSTGRES_HOST: prod-db-server
...
🎯 测试完成！当前使用环境: production (.env)
```