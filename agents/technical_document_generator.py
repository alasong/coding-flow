import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from config import AGENT_CONFIGS, DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class BaseModel:
    """基础模型接口"""
    def __call__(self, prompt: str):
        raise NotImplementedError

class TechnicalDocumentGeneratorAgent:
    """技术文档生成Agent - 生成架构设计相关的技术文档"""
    
    def __init__(self, name: str = "技术文档生成器", model_config_name: str = "technical_document_generator", model: Optional[BaseModel] = None):
        self.name = name
        self.model_config_name = model_config_name
        self.model = model or self._get_default_model()
        self.system_prompt = AGENT_CONFIGS["technical_document_generator"]["system_prompt"]
        logger.info(f"初始化 {self.name}")
        
    def _get_default_model(self):
        """获取默认模型 - 优先使用真实API"""
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 根据API密钥类型选择模型
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                    return model
                else:
                    from agentscope.model import OpenAIChatModel
                    model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                    return model
                    
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.warning(f"[{self.name}] 未配置API密钥，使用离线文档生成（回退内容）")
            return None
    
    async def generate_technical_documents(self, requirements: Dict[str, Any], architecture_design: Dict[str, Any], 
                                     validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成架构设计文档"""
        logger.info("开始生成架构设计文档")
        
        try:
            # 生成架构设计文档
            doc_content = await self._generate_architecture_design_content(requirements, architecture_design, validation_result)
            
            # 生成技术选型文档
            tech_selection_content = await self._generate_tech_selection_content(requirements, architecture_design)
            
            # 生成部署文档
            deployment_content = await self._generate_deployment_content(requirements, architecture_design, validation_result)
            
            # 生成完整的技术文档包
            technical_docs = {
                "architecture_design": doc_content,
                "technology_selection": tech_selection_content,
                "deployment_guide": deployment_content,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            logger.info("技术文档生成完成")
            return technical_docs
            
        except Exception as e:
            logger.error(f"技术文档生成失败: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_architecture_design_content(self, requirements: Dict[str, Any], 
                                            architecture_design: Dict[str, Any], 
                                            validation_result: Dict[str, Any]) -> str:
        """生成架构设计文档内容"""
        
        prompt = f"""
{self.system_prompt}

请基于以下信息生成一份完整的架构设计文档：

## 需求规格
{json.dumps(requirements, ensure_ascii=False, indent=2)}

## 架构设计
{json.dumps(architecture_design, ensure_ascii=False, indent=2)}

## 验证结果
{json.dumps(validation_result, ensure_ascii=False, indent=2)}

## 文档要求
请生成一份专业的架构设计文档，包含以下章节：

1. **文档信息**
   - 文档标题：系统架构设计说明书
   - 版本号：v1.0
   - 创建日期：{datetime.now().strftime('%Y-%m-%d')}
   - 作者：AI架构设计助手

2. **执行摘要**
   - 项目背景和目标
   - 架构设计概述
   - 关键技术决策
   - 主要风险和建议

3. **架构概览**
   - 系统整体架构图
   - 架构风格和设计原则
   - 核心组件和交互关系
   - 数据流和控制流

4. **技术架构**
   - 前端架构设计
   - 后端架构设计
   - 数据库架构设计
   - 缓存架构设计
   - 消息队列架构

5. **部署架构**
   - 基础设施架构
   - 网络拓扑设计
   - 容器化策略
   - 负载均衡设计
   - 高可用性设计

6. **安全架构**
   - 安全架构原则
   - 身份认证设计
   - 访问控制机制
   - 数据加密策略
   - 安全监控方案

7. **性能设计**
   - 性能指标定义
   - 性能优化策略
   - 扩展性设计
   - 负载测试方案

8. **运维架构**
   - 监控告警设计
   - 日志管理策略
   - 故障处理机制
   - 备份恢复方案
   - 变更管理流程

9. **实施计划**
   - 开发阶段划分
   - 里程碑定义
   - 资源需求评估
   - 风险缓解措施

10. **附录**
    - 术语表
    - 参考文档
    - 架构决策记录

请确保文档内容：
- 专业性和技术深度
- 实用性和可操作性
- 完整性和一致性
- 符合行业标准

文档格式要求：
- 使用Markdown格式
- 包含必要的图表和表格
- 清晰的章节结构
- 专业的技术语言
"""

        try:
            response = await self._call_model_with_streaming(prompt)
            return self._format_architecture_document(response)
        except Exception as e:
            logger.error(f"架构设计文档生成失败: {e}")
            return self._generate_fallback_architecture_content(requirements, architecture_design)
    
    async def _generate_tech_selection_content(self, requirements: Dict[str, Any], architecture_design: Dict[str, Any]) -> str:
        """生成技术选型文档内容"""
        
        prompt = f"""
{self.system_prompt}

请基于以下信息生成一份技术选型说明书：

## 需求规格
{json.dumps(requirements, ensure_ascii=False, indent=2)}

## 架构设计
{json.dumps(architecture_design, ensure_ascii=False, indent=2)}

## 文档要求
生成技术选型说明书，包含：

1. **技术选型概述**
   - 选型原则和标准
   - 评估方法论
   - 决策框架

2. **前端技术栈**
   - 框架选择（React/Vue/Angular）
   - UI组件库
   - 状态管理方案
   - 构建工具
   - 测试框架

3. **后端技术栈**
   - 编程语言选择
   - Web框架选择
   - API设计规范
   - 微服务架构
   - 依赖注入框架

4. **数据库技术**
   - 关系型数据库选择
   - NoSQL数据库选择
   - 缓存数据库选择
   - 数据库设计工具

5. **中间件技术**
   - 消息队列选型
   - 搜索引擎选型
   - 日志收集方案
   - 监控告警工具

6. **部署和运维**
   - 容器化技术
   - 编排平台选择
   - CI/CD工具
   - 云服务提供商
   - 监控工具栈

7. **开发工具**
   - 版本控制系统
   - IDE和编辑器
   - 代码质量工具
   - 文档生成工具

8. **选型决策记录**
   - 每个技术选择的理由
   - 备选方案对比
   - 风险评估
   - 学习成本分析

请提供详细的技术对比表格和决策依据。
"""

        try:
            response = await self._call_model_with_streaming(prompt)
            return self._format_technology_selection(response)
        except Exception as e:
            logger.error(f"技术选型文档生成失败: {e}")
            return self._generate_fallback_tech_content(requirements, architecture_design)
    
    async def _generate_deployment_content(self, requirements: Dict[str, Any], 
                                   architecture_design: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> str:
        """生成部署文档内容"""
        
        prompt = f"""
{self.system_prompt}

请基于以下信息生成一份部署指南文档：

## 需求规格
{json.dumps(requirements, ensure_ascii=False, indent=2)}

## 架构设计
{json.dumps(architecture_design, ensure_ascii=False, indent=2)}

## 验证结果
{json.dumps(validation_result, ensure_ascii=False, indent=2)}

## 文档要求
生成详细的部署指南，包含：

1. **部署概述**
   - 部署目标和范围
   - 部署策略和原则
   - 环境规划

2. **基础设施准备**
   - 服务器规格要求
   - 网络配置要求
   - 存储需求
   - 安全组配置

3. **环境搭建**
   - 开发环境搭建
   - 测试环境搭建
   - 预生产环境搭建
   - 生产环境搭建

4. **应用部署**
   - 应用打包流程
   - 容器化部署步骤
   - 服务编排配置
   - 负载均衡配置

5. **数据库部署**
   - 数据库安装配置
   - 数据迁移方案
   - 备份策略配置
   - 性能调优

6. **监控和日志**
   - 监控系统部署
   - 日志收集配置
   - 告警规则设置
   - 仪表板配置

7. **安全配置**
   - SSL证书配置
   - 防火墙配置
   - 访问控制设置
   - 安全扫描

8. **运维流程**
   - 日常维护任务
   - 故障处理流程
   - 变更管理流程
   - 应急响应预案

9. **部署检查清单**
   - 部署前检查项
   - 部署中检查项
   - 部署后验证项
   - 回滚检查项

请提供具体的命令行操作步骤和配置示例。
"""

        try:
            response = await self._call_model_with_streaming(prompt)
            return self._format_deployment_guide(response)
        except Exception as e:
            logger.error(f"部署文档生成失败: {e}")
            return self._generate_fallback_deployment_content(requirements, architecture_design, validation_result)
    
    def _generate_fallback_deployment_content(self, requirements: Dict[str, Any], 
                                        architecture_design: Dict[str, Any], 
                                        validation_result: Dict[str, Any]) -> str:
        """生成部署文档的备用内容"""
        # 提取架构信息
        tech_stack = architecture_design.get("technology_stack", {})
        deployment_info = architecture_design.get("deployment_architecture", {})
        
        # 提取验证结果中的部署建议
        validation_data = validation_result.get("validation_result", {})
        deployment_suggestions = validation_data.get("suggestions", [])
        
        # 过滤部署相关的建议
        deployment_tips = []
        for suggestion in deployment_suggestions:
            if any(keyword in suggestion.lower() for keyword in ['部署', '运维', '监控', '安全']):
                deployment_tips.append(suggestion)
        
        return f"""# 系统部署指南

## 1. 部署概述

### 1.1 Deployment Objectives
This document provides a complete system deployment process to ensure the system can run stably, securely and efficiently in the target environment.

### 1.2 Deployment Scope
- Infrastructure environment setup
- Application containerized deployment
- Database and middleware configuration
- Monitoring and alerting system integration
- Security protection measures configuration

### 1.3 Deployment Principles
- **Automation**: Adopt Infrastructure as Code (IaC) concept
- **Repeatability**: Ensure deployment process can be repeated
- **Monitorability**: Complete monitoring and log collection
- **Rollback**: Support for quick rollback to stable versions

## 2. System Environment Requirements

### 2.1 Hardware Requirements
| Environment Type | CPU | Memory | Storage | Network |
|-----------------|-----|--------|---------|---------|
| Development | 2 cores | 4GB | 50GB | 1Gbps |
| Testing | 4 cores | 8GB | 100GB | 1Gbps |
| Staging | 8 cores | 16GB | 200GB | 1Gbps |
| **Production** | 16+ cores | 32+ GB | 500+ GB | 10Gbps |

### 2.2 Software Requirements
#### 2.2.1 Operating System
- **Recommended**: Ubuntu Server 22.04 LTS / CentOS 8+
- **Kernel Version**: Linux 5.4+
- **File System**: ext4 / XFS

#### 2.2.2 Container Runtime
- **Docker**: 24.0.0+
- **containerd**: 1.7.0+
- **Podman**: 4.0+ (optional)

#### 2.2.3 Container Orchestration
- **Kubernetes**: 1.28+
- **kubectl**: 1.28+
- **Helm**: 3.12+

#### 2.2.4 Monitoring Tools
- **Prometheus**: 2.45+
- **Grafana**: 10.0+
- **Alertmanager**: 0.25+

### 2.3 Network Requirements
- **Internal Communication**: All nodes must be able to communicate
- **External Access**: Necessary public network access permissions
- **Domain Resolution**: DNS configuration required
- **Load Balancing**: Support for Layer 4/7 load balancing

## 3. Basic Environment Preparation

### 3.1 System Initialization
```bash
#!/bin/bash
# System initialization script

# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install basic tools
sudo apt install -y curl wget git vim htop net-tools unzip

# 3. Configure timezone
sudo timedatectl set-timezone Asia/Shanghai

# 4. Configure hostname
sudo hostnamectl set-hostname k8s-master

# 5. Configure hosts file
cat >> /etc/hosts << EOF
192.168.1.10 k8s-master
192.168.1.11 k8s-node1
192.168.1.12 k8s-node2
EOF

# 6. Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# 7. Configure kernel parameters
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
```

### 3.2 Docker Installation and Configuration
```bash
#!/bin/bash
# Docker installation script

# 1. Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# 2. Install dependency packages
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 3. Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. Set up stable repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 6. Configure Docker
cat > /etc/docker/daemon.json << EOF
{{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {{
    "max-size": "100m",
    "max-file": "3"
  }},
  "storage-driver": "overlay2",
  "registry-mirrors": ["https://registry.docker-cn.com"]
}}
EOF

# 7. Start Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker

# 8. Add user to docker group
sudo usermod -aG docker $USER
```

### 3.3 Kubernetes Cluster Initialization
```bash
#!/bin/bash
# Kubernetes installation script

# 1. Add Kubernetes source
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat > /etc/apt/sources.list.d/kubernetes.list << EOF
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF

# 2. Install kubelet, kubeadm, kubectl
sudo apt update
sudo apt install -y kubelet=1.28.0-00 kubeadm=1.28.0-00 kubectl=1.28.0-00
sudo apt-mark hold kubelet kubeadm kubectl

# 3. Initialize Master node
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12

# 4. Configure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 5. Install network plugin (Flannel)
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# 6. Verify cluster status
kubectl get nodes
kubectl get pods --all-namespaces
```

## 4. Application Deployment

### 4.1 Namespace Creation
```bash
#!/bin/bash
# Create namespaces
kubectl create namespace production
kubectl create namespace monitoring
kubectl create namespace logging
```

**Deployment Suggestions**: {deployment_tips[0] if deployment_tips else 'It is recommended to conduct complete validation in the test environment before production deployment'}

**Update Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Version**: v1.0
"""

    async def _generate_deployment_content(self, requirements: Dict[str, Any], 
                                   architecture_design: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> str:
        """生成部署文档内容"""
        try:
            project_name = requirements.get("project_name", "MyProject")
            tech_stack = architecture_design.get("technology_stack", {})
            deployment_info = architecture_design.get("deployment_architecture", {})
            
            # 提取验证结果中的部署建议
            validation_data = validation_result.get("validation_result", {})
            deployment_suggestions = validation_data.get("suggestions", [])
            
            # 过滤部署相关的建议
            deployment_tips = []
            for suggestion in deployment_suggestions:
                if any(keyword in suggestion.lower() for keyword in ['deploy', 'operation', 'monitor', 'security']):
                    deployment_tips.append(suggestion)
            
            prompt = f"""
            基于以下项目信息，生成一份详细的系统部署指南文档：
            
            项目名称: {project_name}
            技术栈: {json.dumps(tech_stack, ensure_ascii=False, indent=2)}
            部署架构: {json.dumps(deployment_info, ensure_ascii=False, indent=2)}
            部署建议: {deployment_tips}
            
            请生成包含以下内容的部署指南：
            1. 部署概述
            2. 系统环境要求
            3. 基础环境准备
            4. 应用程序部署
            5. 数据库部署
            6. 监控和日志系统
            7. 安全配置
            8. 备份和恢复
            9. 运维管理
            10. 部署验证
            
            要求：
            - 提供具体的命令示例和配置文件
            - 包含详细的步骤说明
            - 提供故障排查指南
            - 包含性能优化建议
            - 提供安全最佳实践
            """
            
            # 使用流式调用获取响应
            response_content = ""
            try:
                # 调用模型获取异步迭代器
                response_stream = await self.model([{"role": "user", "content": prompt}])
                
                # 迭代流式响应
                async for chunk in response_stream:
                    if hasattr(chunk, 'content') and chunk.content:
                        # 处理content属性（可能是列表）
                        content = chunk.content
                        if isinstance(content, list) and len(content) > 0:
                            for item in content:
                                if isinstance(item, dict) and 'text' in item:
                                    response_content += item['text']
                                elif hasattr(item, 'text'):
                                    response_content += item.text
                        elif isinstance(content, str):
                            response_content += content
                    elif hasattr(chunk, 'text') and chunk.text:
                        response_content += chunk.text
                    elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        response_content += chunk.message.content
            except Exception as e:
                logger.error(f"流式响应处理失败: {e}")
                return self._generate_fallback_deployment_content(requirements, architecture_design, validation_result)
            
            return response_content.strip()
            
        except Exception as e:
            logger.error(f"部署文档生成失败: {e}")
            return self._generate_fallback_deployment_content(requirements, architecture_design, validation_result)

    def _generate_fallback_deployment_content(self, requirements: Dict[str, Any], 
                                        architecture_design: Dict[str, Any], 
                                        validation_result: Dict[str, Any]) -> str:
        """生成部署文档的备用内容"""
        # 提取架构信息
        tech_stack = architecture_design.get("technology_stack", {})
        deployment_info = architecture_design.get("deployment_architecture", {})
        
        # 提取验证结果中的部署建议
        validation_data = validation_result.get("validation_result", {})
        deployment_suggestions = validation_data.get("suggestions", [])
        
        # 过滤部署相关的建议
        deployment_tips = []
        for suggestion in deployment_suggestions:
            if any(keyword in suggestion.lower() for keyword in ['deploy', 'operation', 'monitor', 'security']):
                deployment_tips.append(suggestion)
        
        return f"""# System Deployment Guide

## 1. Deployment Overview

### 1.1 Deployment Objectives
This document provides a complete system deployment process to ensure the system can run stably, securely and efficiently in the target environment.

### 1.2 Deployment Scope
- Infrastructure environment setup
- Application containerized deployment
- Database and middleware configuration
- Monitoring and alerting system integration
- Security protection measures configuration

### 1.3 Deployment Principles
- **Automation**: Adopt Infrastructure as Code (IaC) concept
- **Repeatability**: Ensure deployment process can be repeated
- **Monitorability**: Complete monitoring and log collection
- **Rollback**: Support for quick rollback to stable versions

## 2. System Environment Requirements

### 2.1 Hardware Requirements
| Environment Type | CPU | Memory | Storage | Network |
|-----------------|-----|--------|---------|---------|
| Development | 2 cores | 4GB | 50GB | 1Gbps |
| Testing | 4 cores | 8GB | 100GB | 1Gbps |
| Staging | 8 cores | 16GB | 200GB | 1Gbps |
| **Production** | 16+ cores | 32+ GB | 500+ GB | 10Gbps |

### 2.2 Software Requirements
#### 2.2.1 Operating System
- **Recommended**: Ubuntu Server 22.04 LTS / CentOS 8+
- **Kernel Version**: Linux 5.4+
- **File System**: ext4 / XFS

#### 2.2.2 Container Runtime
- **Docker**: 24.0.0+
- **containerd**: 1.7.0+
- **Podman**: 4.0+ (optional)

#### 2.2.3 Container Orchestration
- **Kubernetes**: 1.28+
- **kubectl**: 1.28+
- **Helm**: 3.12+

#### 2.2.4 Monitoring Tools
- **Prometheus**: 2.45+
- **Grafana**: 10.0+
- **Alertmanager**: 0.25+

### 2.3 Network Requirements
- **Internal Communication**: All nodes must be able to communicate
- **External Access**: Necessary public network access permissions
- **Domain Resolution**: DNS configuration required
- **Load Balancing**: Support for Layer 4/7 load balancing

## 3. Basic Environment Preparation

### 3.1 System Initialization
```bash
#!/bin/bash
# System initialization script

# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install basic tools
sudo apt install -y curl wget git vim htop net-tools unzip

# 3. Configure timezone
sudo timedatectl set-timezone Asia/Shanghai

# 4. Configure hostname
sudo hostnamectl set-hostname k8s-master

# 5. Configure hosts file
cat >> /etc/hosts << EOF
192.168.1.10 k8s-master
192.168.1.11 k8s-node1
192.168.1.12 k8s-node2
EOF

# 6. Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# 7. Configure kernel parameters
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
```

### 3.2 Docker Installation and Configuration
```bash
#!/bin/bash
# Docker installation script

# 1. Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# 2. Install dependency packages
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 3. Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. Set up stable repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 6. Configure Docker
cat > /etc/docker/daemon.json << EOF
{{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {{
    "max-size": "100m",
    "max-file": "3"
  }},
  "storage-driver": "overlay2",
  "registry-mirrors": ["https://registry.docker-cn.com"]
}}
EOF

# 7. Start Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
sudo systemctl enable docker

# 8. Add user to docker group
sudo usermod -aG docker $USER
```

### 3.3 Kubernetes Cluster Initialization
```bash
#!/bin/bash
# Kubernetes installation script

# 1. Add Kubernetes source
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
cat > /etc/apt/sources.list.d/kubernetes.list << EOF
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF

# 2. Install kubelet, kubeadm, kubectl
sudo apt update
sudo apt install -y kubelet=1.28.0-00 kubeadm=1.28.0-00 kubectl=1.28.0-00
sudo apt-mark hold kubelet kubeadm kubectl

# 3. Initialize Master node
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12

# 4. Configure kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 5. Install network plugin (Flannel)
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml

# 6. Verify cluster status
kubectl get nodes
kubectl get pods --all-namespaces
```

## 4. Application Deployment

### 4.1 Namespace Creation
```bash
#!/bin/bash
# Create namespaces
kubectl create namespace production
kubectl create namespace monitoring
kubectl create namespace logging
```
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  # 应用配置
  APP_ENV: "production"
  APP_DEBUG: "false"
  APP_URL: "https://api.example.com"
  
  # 数据库配置
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "app_production"
  
  # Redis配置
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  
  # 日志配置
  LOG_LEVEL: "info"
  LOG_FORMAT: "json"
```

### 4.3 密钥管理
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
data:
  # Base64编码的敏感信息
  DB_PASSWORD: cGFzc3dvcmQxMjM=  # password123
  JWT_SECRET: c3VwZXJzZWNyZXRqd3RrZXk=  # supersecretjwtkey
  API_KEY: bXlzZWNyZXRhcGlrZXk=  # mysecretapikey
```

### 4.4 应用部署配置
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-backend
  namespace: production
  labels:
    app: backend
    tier: backend
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v1.0.0
    spec:
      containers:
      - name: backend
        image: registry.example.com/app/backend:v1.0.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: APP_ENV
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: DB_PASSWORD
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: app-logs
          mountPath: /app/logs
      volumes:
      - name: app-logs
        emptyDir: {{}}
      imagePullSecrets:
      - name: registry-secret
```

### 4.5 服务暴露
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: production
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: backend

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: app-tls-secret
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
```

## 5. 数据库部署

### 5.1 PostgreSQL部署
```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: app_production
        - name: POSTGRES_USER
          value: appuser
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd
```

### 5.2 Redis部署
```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --maxmemory
        - 2gb
        - --maxmemory-policy
        - allkeys-lru
        - --save
        - "900 1"
        - --save
        - "300 10"
        - --save
        - "60 10000"
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
```

## 6. 监控和日志系统

### 6.1 Prometheus部署
```yaml
# prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.45.0
        ports:
        - containerPort: 9090
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--storage.tsdb.retention.time=30d'
        - '--web.enable-lifecycle'
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

### 6.2 Grafana部署
```yaml
# grafana-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.0.0
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secret
              key: admin-password
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
      volumes:
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc
```

## 7. 安全配置

### 7.1 网络策略
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
```

### 7.2 Pod安全策略
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

## 8. 备份和恢复

### 8.1 数据库备份
```bash
#!/bin/bash
# 数据库备份脚本

# PostgreSQL备份
kubectl exec -n production postgres-0 -- pg_dump -U appuser app_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis备份  
kubectl exec -n production redis-0 -- redis-cli save
cp /data/dump.rdb backup_redis_$(date +%Y%m%d_%H%M%S).rdb

# 上传到云存储
aws s3 cp backup_*.sql s3://backups/postgres/
aws s3 cp backup_*.rdb s3://backups/redis/
```

### 8.2 应用配置备份
```bash
#!/bin/bash
# 配置备份脚本

# 备份所有ConfigMap和Secret
kubectl get configmap -A -o yaml > configmaps_backup.yaml
kubectl get secret -A -o yaml > secrets_backup.yaml

# 备份Ingress配置
kubectl get ingress -A -o yaml > ingress_backup.yaml

# 压缩备份文件
tar -czf k8s_config_backup_$(date +%Y%m%d_%H%M%S).tar.gz *.yaml

# 上传到安全存储
aws s3 cp k8s_config_backup_*.tar.gz s3://backups/kubernetes/
```

## 9. 运维管理

### 9.1 日常维护清单
- [ ] 检查所有Pod运行状态
- [ ] 验证服务可用性
- [ ] 检查资源使用情况
- [ ] 查看应用日志
- [ ] 验证监控告警
- [ ] 检查备份任务

### 9.2 故障排查指南
```bash
# 1. 检查Pod状态
kubectl get pods -A | grep -v Running

# 2. 查看Pod日志
kubectl logs <pod-name> -n <namespace> --tail=100

# 3. 检查服务状态
kubectl get svc -A

# 4. 检查Ingress状态
kubectl get ingress -A

# 5. 检查资源使用
kubectl top nodes
kubectl top pods -A

# 6. 检查事件
kubectl get events -A --sort-by='.lastTimestamp'
```

### 9.3 扩容缩容操作
```bash
# 手动扩容
kubectl scale deployment app-backend --replicas=5 -n production

# 自动扩缩容配置
kubectl autoscale deployment app-backend --min=3 --max=10 --cpu-percent=70 -n production

# 查看HPA状态
kubectl get hpa -n production
```

## 10. 部署验证

### 10.1 功能验证清单
- [ ] API接口测试
- [ ] 数据库连接测试
- [ ] 缓存服务测试
- [ ] 消息队列测试
- [ ] 文件上传下载测试
- [ ] 用户认证测试
- [ ] 权限控制测试

### 10.2 性能验证
```bash
# 使用Apache Bench进行压力测试
ab -n 10000 -c 100 https://api.example.com/health

# 使用wrk进行高性能测试
wrk -t12 -c400 -d30s https://api.example.com/api/users

# 使用k6进行现代负载测试
k6 run --vus 100 --duration 30s load-test.js
```

### 10.3 安全验证
- [ ] SSL证书有效性
- [ ] 端口扫描检测
- [ ] 漏洞扫描
- [ ] 权限验证
- [ ] 输入验证测试
- [ ] SQL注入测试

---

## 附录

### A. 部署脚本集合
```bash
# 一键部署脚本
#!/bin/bash
set -e

echo "开始部署系统..."

# 1. 环境检查
./scripts/environment-check.sh

# 2. 创建命名空间
kubectl apply -f manifests/namespaces.yaml

# 3. 部署配置和密钥
kubectl apply -f manifests/configmaps/
kubectl apply -f manifests/secrets/

# 4. 部署数据库
kubectl apply -f manifests/databases/

# 5. 部署应用服务
kubectl apply -f manifests/applications/

# 6. 部署监控告警
kubectl apply -f manifests/monitoring/

# 7. 部署Ingress
kubectl apply -f manifests/ingress/

echo "部署完成！"
```

### B. 故障处理手册
```bash
# 常见故障处理

# Pod无法启动
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>

# 服务无法访问
kubectl get svc -n <namespace>
kubectl get endpoints <service-name> -n <namespace>

# Ingress无法访问
kubectl get ingress -n <namespace>
kubectl describe ingress <ingress-name> -n <namespace>

# 节点NotReady
kubectl describe node <node-name>
sudo journalctl -u kubelet
```

### C. 联系方式
- **技术支持**: support@example.com
- **运维团队**: ops@example.com
- **安全团队**: security@example.com
- **紧急联系**: +86-400-123-4567

---

**部署建议**: {deployment_tips[0] if deployment_tips else '建议在生产环境部署前，先在测试环境进行完整验证'}

**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**版本**: v1.0
"""

    async def _call_model_with_streaming(self, prompt: str) -> str:
        """调用模型并处理流式响应"""
        try:
            logger.debug(f"调用模型: {self.name}")
            
            # 调用模型 - DashScopeChatModel的正确调用方式
            response = await self.model([{"role": "user", "content": prompt}])
            
            # 处理流式响应
            content = ""
            
            # 检查响应类型
            if isinstance(response, str):
                # 如果直接返回字符串
                return response
            elif hasattr(response, 'content'):
                # 如果响应对象有content属性
                if isinstance(response.content, str):
                    return response.content
                elif isinstance(response.content, list):
                    # content是[{"type": "text", "text": "..."}]格式
                    for item in response.content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            content += item.get('text', '')
                        else:
                            content += str(item)
                    return content
                else:
                    # 如果content是其他类型，尝试转换为字符串
                    return str(response.content)
            elif hasattr(response, 'text') and isinstance(response.text, str):
                # 如果响应对象有text属性
                return response.text
            elif hasattr(response, 'text'):
                # 如果text属性存在但不是字符串
                return str(response.text)
            else:
                # 检查响应是否可以直接迭代（流式响应）
                if hasattr(response, '__aiter__'):
                    # 处理异步迭代器（流式响应）
                    try:
                        full_content = ""
                        last_content = ""
                        
                        async for chunk in response:
                            # DashScopeChatModel返回的是ChatResponse对象，content属性是列表
                            if hasattr(chunk, 'content') and isinstance(chunk.content, list):
                                # content是[{"type": "text", "text": "..."}]格式
                                current_content = ""
                                for item in chunk.content:
                                    if isinstance(item, dict) and item.get('type') == 'text':
                                        current_content += item.get('text', '')
                                    else:
                                        current_content += str(item)
                                # 只保留完整内容，避免增量累积
                                if len(current_content) > len(last_content):
                                    full_content = current_content
                                last_content = current_content
                            elif hasattr(chunk, 'text'):
                                current_content = chunk.text if isinstance(chunk.text, str) else str(chunk.text)
                                # 只保留完整内容，避免增量累积
                                if len(current_content) > len(last_content):
                                    full_content = current_content
                                last_content = current_content
                            elif hasattr(chunk, 'message'):
                                current_content = str(chunk.message)
                                # 只保留完整内容，避免增量累积
                                if len(current_content) > len(last_content):
                                    full_content = current_content
                                last_content = current_content
                            elif isinstance(chunk, str):
                                # 如果是字符串，直接作为完整内容
                                full_content = chunk
                                last_content = chunk
                            else:
                                # 如果没有可识别的属性，尝试转换为字符串
                                current_content = str(chunk)
                                if len(current_content) > len(last_content):
                                    full_content = current_content
                                last_content = current_content
                        
                        return full_content
                    except Exception as stream_error:
                        logger.warning(f"流式处理失败，尝试直接返回响应: {stream_error}")
                        # 如果流式处理失败，尝试直接返回响应的字符串表示
                        return str(response)
                else:
                    # 如果响应对象既不是字符串也没有content/text属性，也不是可异步迭代的
                    # 尝试检查是否有其他可能的属性
                    logger.warning(f"无法识别的响应类型: {type(response)}")
                    
                    # 首先尝试直接访问响应对象，看是否是字典或类似结构
                    try:
                        # 尝试将响应转换为字典
                        response_dict = dict(response) if hasattr(response, '__dict__') else None
                        if response_dict:
                            # 如果是字典，尝试获取常见的键
                            for key in ['content', 'text', 'message', 'data', 'result', 'output', 'response']:
                                if key in response_dict:
                                    value = response_dict[key]
                                    if isinstance(value, str):
                                        return value
                                    else:
                                        return str(value)
                    except Exception:
                        pass
                    
                    # 尝试一些常见的属性名
                    for attr_name in ['data', 'result', 'output', 'response']:
                        if hasattr(response, attr_name):
                            attr_value = getattr(response, attr_name)
                            if isinstance(attr_value, str):
                                return attr_value
                            else:
                                return str(attr_value)
                    
                    # 如果所有尝试都失败，返回字符串表示
                    return str(response)
            
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            raise

    def _generate_fallback_architecture_content(self, requirements: Dict[str, Any], 
                                              architecture_design: Dict[str, Any]) -> str:
        """生成架构设计文档的备用内容"""
        try:
            logger.info("生成架构设计文档备用内容")
            
            # 提取架构信息
            components = architecture_design.get("components", [])
            tech_stack = architecture_design.get("technology_stack", {})
            
            doc_content = f"""# 系统架构设计说明书

## 1. 执行摘要

### 项目背景
基于用户需求分析，设计一套现代化的软件系统架构。

### 架构概述
系统采用分层架构设计，包含前端展示层、业务逻辑层、数据访问层和基础设施层。

### 关键技术决策
- 前端框架: {tech_stack.get('frontend', 'React')}
- 后端框架: {tech_stack.get('backend', 'Spring Boot')}
- 数据库: {tech_stack.get('database', 'PostgreSQL')}
- 部署平台: {tech_stack.get('deployment', 'Kubernetes')}

## 2. 架构概览

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端层       │    │   应用层       │    │   数据层       │
│                │────│                │────│                │
│  Web/Mobile    │    │  API Gateway   │    │   Database     │
│                │    │  Microservices │    │   Cache        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件
"""
            
            # 添加组件信息
            for component in components:
                doc_content += f"""
#### {component.get('name', '未知组件')}
- 类型: {component.get('type', '未知')}
- 技术栈: {component.get('technology', '待定')}
- 职责: {component.get('description', '待完善')}
"""
            
            doc_content += f"""

## 3. 技术架构

### 前端架构
- 框架选择: {tech_stack.get('frontend', 'React 18')}
- 状态管理: Redux Toolkit
- UI组件库: Ant Design
- 构建工具: Vite

### 后端架构  
- 框架选择: {tech_stack.get('backend', 'Spring Boot 3.x')}
- API设计: RESTful + GraphQL
- 认证授权: JWT + OAuth2
- 消息队列: {tech_stack.get('message_queue', 'RabbitMQ')}

### 数据库架构
- 主数据库: {tech_stack.get('database', 'PostgreSQL 15')}
- 缓存数据库: {tech_stack.get('cache', 'Redis 7')}
- 连接池: HikariCP
- ORM框架: JPA/Hibernate

## 4. 部署架构

### 基础设施
- 容器平台: {tech_stack.get('container', 'Docker')}
- 编排系统: {tech_stack.get('orchestration', 'Kubernetes')}
- 服务网格: Istio
- 镜像仓库: Harbor

### 网络拓扑
- 负载均衡: Nginx + HAProxy
- API网关: Kong
- 服务发现: Consul
- 配置中心: Nacos

## 5. 安全架构

### 安全原则
- 零信任架构
- 最小权限原则
- 深度防御策略
- 安全左移

### 身份认证
- 多因子认证
- 单点登录(SSO)
- 会话管理
- 密码策略

## 6. 性能设计

### 性能指标
- 响应时间: < 200ms
- 吞吐量: > 1000 TPS
- 并发用户: > 10000
- 可用性: > 99.9%

### 优化策略
- 缓存策略: 多级缓存
- 数据库优化: 索引优化
- 代码优化: 异步处理
- 网络优化: CDN加速

## 7. 运维架构

### 监控告警
- 指标监控: Prometheus + Grafana
- 日志收集: ELK Stack
- 链路追踪: Jaeger
- 告警通知: AlertManager

### 备份恢复
- 数据备份: 定期全量+增量
- 灾难恢复: 多地域部署
- 故障转移: 自动切换
- 数据一致性: 强一致性

## 8. 实施计划

### 开发阶段
1. 需求分析 (2周)
2. 架构设计 (1周)
3. 开发实现 (8周)
4. 测试验证 (3周)
5. 上线部署 (1周)

### 里程碑
- M1: 架构设计完成
- M2: 核心功能开发完成
- M3: 系统集成测试完成
- M4: 生产环境上线

## 9. 风险评估

### 技术风险
- 新技术学习成本
- 第三方服务依赖
- 性能瓶颈风险
- 安全漏洞风险

### 缓解措施
- 技术预研和POC
- 多供应商策略
- 性能测试验证
- 安全扫描和渗透测试

## 10. 附录

### 术语表
- API: Application Programming Interface
- CDN: Content Delivery Network
- HA: High Availability
- SLA: Service Level Agreement

### 参考文档
- [架构设计原则](https://example.com/architecture-principles)
- [技术选型指南](https://example.com/tech-selection)
- [安全最佳实践](https://example.com/security-best-practices)

---

**创建日期**: {datetime.now().strftime('%Y-%m-%d')}
**版本**: v1.0
**作者**: AI架构设计助手
"""
            
            return doc_content
            
        except Exception as e:
            logger.error(f"架构设计备用内容生成失败: {e}")
            return f"# 架构设计文档\n\n由于生成过程中出现错误，这里提供简化的架构设计文档。\n\n**错误信息**: {str(e)}\n\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _format_architecture_document(self, content: str) -> str:
        """格式化架构设计文档"""
        try:
            # 首先确保content是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 基本的文档格式化
            if not content.strip():
                return "# 架构设计文档\n\n文档内容为空。"
            
            # 确保文档有基本的结构
            if not content.startswith("#"):
                content = f"# 系统架构设计说明书\n\n{content}"
            
            # 添加页脚信息
            if "**创建日期**" not in content:
                content += f"\n\n---\n\n**创建日期**: {datetime.now().strftime('%Y-%m-%d')}\n**版本**: v1.0"
            
            return content
            
        except Exception as e:
            logger.error(f"架构文档格式化失败: {e}")
            # 如果格式化失败，至少返回原始内容的字符串表示
            return str(content) if not isinstance(content, str) else content

    def _format_technology_selection(self, content: str) -> str:
        """格式化技术选型文档"""
        try:
            # 首先确保content是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 基本的文档格式化
            if not content.strip():
                return "# 技术选型说明书\n\n文档内容为空。"
            
            # 确保文档有基本的结构
            if not content.startswith("#"):
                content = f"# 技术选型说明书\n\n{content}"
            
            # 添加页脚信息
            if "**创建日期**" not in content:
                content += f"\n\n---\n\n**创建日期**: {datetime.now().strftime('%Y-%m-%d')}\n**版本**: v1.0"
            
            return content
            
        except Exception as e:
            logger.error(f"技术选型文档格式化失败: {e}")
            # 如果格式化失败，至少返回原始内容的字符串表示
            return str(content) if not isinstance(content, str) else content

    def _generate_fallback_tech_content(self, requirements: Dict[str, Any], 
                                     architecture_design: Dict[str, Any]) -> str:
        """生成技术选型文档的备用内容"""
        try:
            logger.info("生成技术选型备用内容")
            
            tech_stack = architecture_design.get("technology_stack", {})
            
            return f"""# 技术选型说明书

## 1. 技术选型概述

### 选型原则
- 成熟稳定: 选择经过验证的成熟技术
- 社区活跃: 拥有活跃的开发者社区
- 学习成本: 团队技术栈匹配度高
- 性能要求: 满足系统性能需求
- 可维护性: 易于维护和扩展

### 评估标准
- 功能性: 是否满足业务需求
- 可靠性: 系统稳定性和容错能力
- 性能: 响应时间和吞吐量
- 安全性: 安全特性和漏洞历史
- 成本: 开发、部署和维护成本

## 2. 前端技术栈

### 框架选择: {tech_stack.get('frontend', 'React 18')}
**选择理由:**
- 组件化开发，提高开发效率
- 虚拟DOM，性能优秀
- 生态系统完善
- 社区活跃，学习资源丰富

**替代方案:** Vue.js, Angular

### UI组件库: Ant Design
**选择理由:**
- 企业级UI设计语言
- 组件丰富，覆盖常见场景
- 支持主题定制
- 文档完善，示例丰富

**替代方案:** Material-UI, Element Plus

### 状态管理: Redux Toolkit
**选择理由:**
- 简化Redux使用
- 内置最佳实践
- TypeScript支持良好
- 开发工具完善

**替代方案:** Zustand, Jotai

## 3. 后端技术栈

### 框架选择: {tech_stack.get('backend', 'Spring Boot 3.x')}
**选择理由:**
- 快速开发和部署
- 自动配置，简化开发
- 微服务架构支持
- 生态系统成熟

**替代方案:** Node.js Express, Django

### 数据库: {tech_stack.get('database', 'PostgreSQL 15')}
**选择理由:**
- 开源免费，成本可控
- 功能强大，支持复杂查询
- 扩展性好，支持分区表
- 社区活跃，文档完善

**替代方案:** MySQL, MongoDB

### 缓存: {tech_stack.get('cache', 'Redis 7')}
**选择理由:**
- 内存数据库，性能优秀
- 支持多种数据结构
- 持久化支持，数据安全
- 集群模式，高可用

**替代方案:** Memcached, Hazelcast

### 消息队列: {tech_stack.get('message_queue', 'RabbitMQ')}
**选择理由:**
- 可靠性高，消息不丢失
- 支持多种消息模式
- 管理界面友好
- 客户端丰富

**替代方案:** Apache Kafka, Apache Pulsar

## 4. 基础设施

### 容器化: {tech_stack.get('container', 'Docker')}
**选择理由:**
- 应用打包标准化
- 环境一致性保证
- 资源隔离性好
- 生态系统完善

**替代方案:** Podman, containerd

### 编排系统: {tech_stack.get('orchestration', 'Kubernetes')}
**选择理由:**
- 容器编排标准
- 自动扩缩容
- 服务发现和负载均衡
- 滚动升级和回滚

**替代方案:** Docker Swarm, Apache Mesos

### 云服务: AWS
**选择理由:**
- 服务种类丰富
- 全球基础设施
- 安全合规认证
- 技术支持完善

**替代方案:** 阿里云, 腾讯云

## 5. 开发工具

### 版本控制: Git
**选择理由:**
- 分布式版本控制
- 分支管理灵活
- 协作开发便利
- 社区标准工具

### CI/CD: Jenkins
**选择理由:**
- 开源免费
- 插件生态丰富
- 支持多种构建方式
- 可扩展性强

**替代方案:** GitLab CI, GitHub Actions

### 代码质量: SonarQube
**选择理由:**
- 代码质量检测
- 技术债务管理
- 多语言支持
- 集成方便

## 6. 风险评估

### 技术风险
- 新技术学习成本
- 第三方依赖风险
- 性能瓶颈风险
- 安全漏洞风险

### 缓解措施
- 技术预研和培训
- 多供应商策略
- 性能测试验证
- 安全扫描和监控

## 7. 实施建议

### 渐进式采用
- 先在非核心系统试用
- 逐步扩大使用范围
- 建立最佳实践
- 团队技能培训

### 监控评估
- 建立技术指标
- 定期评估效果
- 及时调整策略
- 持续优化改进

---

**创建日期**: {datetime.now().strftime('%Y-%m-%d')}
**版本**: v1.0
**作者**: AI架构设计助手
"""
            
        except Exception as e:
            logger.error(f"技术选型备用内容生成失败: {e}")
            return f"# 技术选型说明书\n\n由于生成过程中出现错误，这里提供简化的技术选型文档。\n\n**错误信息**: {str(e)}\n\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"



