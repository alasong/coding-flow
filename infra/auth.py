"""API 认证模块"""

import os
import time
import logging
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_api_key() -> str:
    """获取当前配置的 API Key"""
    return os.getenv("API_KEY", "")


def _is_auth_enabled() -> bool:
    """检查认证是否启用"""
    return os.getenv("API_KEY_ENABLED", "false").lower() == "true"


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> bool:
    """
    验证 API Key
    
    Args:
        api_key: 请求头中的 API Key
        
    Returns:
        验证通过返回 True
        
    Raises:
        HTTPException: API Key 无效时抛出 401 错误
    """
    if not _is_auth_enabled():
        return True

    configured_key = _get_api_key()
    if not api_key or api_key != configured_key:
        logger.warning("API Key 验证失败")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key"
        )
    return True


def verify_ws_token(token: str) -> bool:
    """
    验证 WebSocket 连接 token
    
    使用简单的时间戳验证机制：
    - token = API_KEY + timestamp（10位时间戳）
    - 有效期 5 分钟
    
    Args:
        token: WebSocket 连接时携带的 token
        
    Returns:
        验证通过返回 True，否则返回 False
    """
    if not _is_auth_enabled():
        return True

    configured_key = _get_api_key()
    
    if not token or len(token) < 10:
        logger.warning("WebSocket token 格式无效")
        return False

    try:
        key_part = token[:-10]
        ts_part = int(token[-10:])

        # 检查时间戳（5分钟有效期）
        if abs(time.time() - ts_part) > 300:
            logger.warning("WebSocket token 已过期")
            return False

        if key_part != configured_key:
            logger.warning("WebSocket token API Key 不匹配")
            return False

        return True
    except (ValueError, TypeError) as e:
        logger.warning(f"WebSocket token 解析失败: {e}")
        return False


def generate_ws_token() -> str:
    """
    生成 WebSocket 连接 token
    
    Returns:
        token = API_KEY + 当前时间戳
    """
    api_key = _get_api_key()
    if not api_key:
        return ""
    return f"{api_key}{int(time.time())}"
