# 技术栈扫描字段映射指南

本文件指导 LLM 如何从 scan-result.json 中提取各技术栈的信息，合成知识库文档。

---

## Java/Spring

scan-result.json 中的关键字段及其用途：

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `build.group_id / artifact_id / modules` | 项目概要 | architecture.md |
| `controllers[].methods[]` | API 路由（http_method + http_path + 方法签名） | symbols.md, .scan-snapshot.md |
| `services[].methods[]` | 核心业务方法 | symbols.md, .scan-snapshot.md |
| `repositories[]` | 数据访问层 | symbols.md |
| `entities[]` | 数据模型（class_name + table_name + fields） | database-schema.md, .scan-snapshot.md |
| `cross_service_calls[]` | 跨服务调用关系（target_app_id + type + methods） | call-chains.md, cross-service.md |
| `mq[]` | 消息队列使用（topic + direction） | call-chains.md |
| `scheduled_tasks[]` | 定时任务 | call-chains.md |
| `sql_files[]` | 数据库 DDL | database-schema.md |
| `enums[]` | 枚举定义 | database-schema.md, glossary.md |
| `config_files[]` | 配置项 | .scan-snapshot.md |
| `directory_tree` | 模块结构 | architecture.md, codebase-index.md |

### Controller 方法提取示例

```json
{
  "class_name": "ContractController",
  "file_path": "src/main/java/.../ContractController.java",
  "base_mapping": "/api/contract",
  "methods": [
    {
      "name": "createContract",
      "http_method": "POST",
      "http_path": "/api/contract/create",
      "params": "CreateContractRequest request",
      "return_type": "Response<ContractDTO>",
      "line": 45,
      "body_preview": "contractService.create(request)..."
    }
  ]
}
```

→ symbols.md 输出:
```
| ContractController | createContract(CreateContractRequest): Response<ContractDTO> | src/.../ContractController.java:45 | 创建合同 |
```

### 跨服务调用提取

```json
{
  "type": "AmsMeshClient",
  "target_app_id": "payment-srv",
  "interface_class": "PaymentClient",
  "methods": ["pay", "refund"]
}
```

→ call-chains.md 跨服务调用表:
```
| payment-srv | AmsMeshClient | pay(), refund() | 支付和退款 |
```

---

## PHP

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `composer` | 框架和依赖 | architecture.md |
| `routes[]` | 路由定义 | .scan-snapshot.md |
| `controllers[]` | Controller 和方法 | symbols.md |
| `models[]` | 数据模型 | symbols.md, database-schema.md |
| `config_files[]` | 配置文件 | .scan-snapshot.md |
| `migrations[]` | 数据库迁移 | database-schema.md |

---

## Go

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `go_mod` | 模块名和依赖 | architecture.md |
| `handlers[]` | HTTP handler | symbols.md |
| `structs[]` | 数据结构 | symbols.md, database-schema.md |
| `grpc_services[]` | gRPC 服务 | symbols.md, call-chains.md |
| `sql_files[]` | SQL 文件 | database-schema.md |

---

## 前端 (Vue/React)

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `framework` | 框架版本 | architecture.md |
| `routes[]` | 前端路由 | symbols.md |
| `api_calls[]` | API 调用层 | call-chains.md |
| `store` | 状态管理 | architecture.md |
| `pages[]` | 页面组件 | codebase-index.md |

---

## Node.js (Express/NestJS/Koa)

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `routes[]` | 路由定义 | symbols.md |
| `controllers[]` | Controller | symbols.md |
| `models[]` | 数据模型 | database-schema.md |
| `middleware[]` | 中间件 | architecture.md |

---

## Python (Django/Flask/FastAPI)

| JSON 字段 | 提取内容 | 目标文档 |
|-----------|---------|---------|
| `dependencies` | 依赖 | architecture.md |
| `routes[]` | 路由/视图 | symbols.md |
| `models[]` | 数据模型 | database-schema.md |
| `config` | 配置 | .scan-snapshot.md |
