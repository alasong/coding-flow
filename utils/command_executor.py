"""安全的命令执行工具"""

import subprocess
import logging
import shlex
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# 允许执行的命令白名单
ALLOWED_COMMANDS = {
    "docker": ["compose", "up", "down", "-d", "--build", "--force-recreate"],
}

class CommandExecutionError(Exception):
    """命令执行错误"""
    pass

def validate_command(command: str) -> Tuple[str, List[str]]:
    """
    验证并解析命令，返回 (主命令, 参数列表)
    
    Args:
        command: 要验证的命令字符串
        
    Returns:
        (主命令, 参数列表)
        
    Raises:
        CommandExecutionError: 命令不在白名单中或格式无效
    """
    # 检查危险的 shell 特殊字符
    dangerous_chars = [';', '&&', '||', '|', '`', '$', '>', '<', '\n', '\r']
    for char in dangerous_chars:
        if char in command:
            raise CommandExecutionError(f"命令包含危险字符: {repr(char)}")
    
    parts = shlex.split(command)
    if not parts:
        raise CommandExecutionError("空命令")

    main_cmd = parts[0]
    if main_cmd not in ALLOWED_COMMANDS:
        raise CommandExecutionError(f"不允许执行的命令: {main_cmd}")

    # 验证参数是否在允许列表中
    allowed_args = ALLOWED_COMMANDS[main_cmd]
    for arg in parts[1:]:
        if arg.startswith("-") and arg not in allowed_args:
            raise CommandExecutionError(f"不允许的参数: {arg}")

    return main_cmd, parts[1:]

def safe_execute(command: str, cwd: str, timeout: int = 60) -> Tuple[int, str, str]:
    """
    安全执行命令（不使用 shell=True）
    
    Args:
        command: 要执行的命令字符串
        cwd: 工作目录
        timeout: 超时时间（秒）
        
    Returns:
        (return_code, stdout, stderr)
        
    Raises:
        CommandExecutionError: 命令执行失败
    """
    main_cmd, args = validate_command(command)

    logger.info(f"执行命令: {main_cmd} {' '.join(args)}")

    try:
        result = subprocess.run(
            [main_cmd] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # 关键：不使用 shell
        )
        if result.returncode != 0:
            logger.warning(f"命令返回非零状态码: {result.returncode}, stderr: {result.stderr}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        logger.error(f"命令执行超时: {command}")
        raise CommandExecutionError(f"命令执行超时: {command}")
    except FileNotFoundError as e:
        logger.error(f"命令不存在: {main_cmd}")
        raise CommandExecutionError(f"命令不存在: {main_cmd}")
    except Exception as e:
        logger.error(f"命令执行异常: {e}")
        raise CommandExecutionError(f"命令执行异常: {e}")

def safe_docker_compose(action: str, cwd: str, timeout: int = 120) -> Tuple[int, str, str]:
    """
    安全执行 docker compose 命令
    
    Args:
        action: 动作类型，支持 'up' 或 'down'
        cwd: docker-compose.yml 所在目录
        timeout: 超时时间（秒）
        
    Returns:
        (return_code, stdout, stderr)
    """
    if action not in ["up", "down"]:
        raise CommandExecutionError(f"不支持的 docker compose 动作: {action}")
    
    if action == "up":
        command = "docker compose up -d"
    else:
        command = "docker compose down"
    
    return safe_execute(command, cwd, timeout)
