import logging
import json
from datetime import datetime
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """设置日志配置"""
    import os
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )

def get_project_slug(input_text: str) -> str:
    """根据输入生成项目目录slug，尽量可读，必要时回退到哈希"""
    import re
    import hashlib
    base = (input_text or "").strip()
    for line in base.splitlines():
        if "项目名称" in line or "Project Name" in line:
            name = line.split(':')[-1].strip()
            slug = re.sub(r'[^a-zA-Z0-9\-]+', '-', name)
            slug = slug.strip('-')
            if len(slug) >= 3:
                return slug[:60]
    h = hashlib.md5((input_text or "").encode('utf-8')).hexdigest()[:8]
    return f"project-{h}"

def save_json_data(data: Dict[str, Any], filename: str, output_dir: str = "./output") -> str:
    """保存JSON数据到文件"""
    import os
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

def load_json_data(filepath: str) -> Dict[str, Any]:
    """从文件加载JSON数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_requirement_output(requirements: Dict[str, Any]) -> str:
    """格式化需求输出"""
    output = []
    output.append("=" * 50)
    output.append("需求分析结果")
    output.append("=" * 50)
    
    for category, items in requirements.items():
        if items:
            output.append(f"\n{category.replace('_', ' ').title()}:")
            for i, item in enumerate(items, 1):
                output.append(f"  {i}. {item}")
    
    return "\n".join(output)

def validate_user_input(user_input: str) -> bool:
    """验证用户输入"""
    if not user_input or len(user_input.strip()) < 10:
        return False
    
    # 检查是否包含基本的需求信息
    keywords = ["功能", "系统", "需要", "要求", "应该", "必须"]
    return any(keyword in user_input for keyword in keywords)
