#!/usr/bin/env python3
import asyncio
import os
import sys
import shutil
import subprocess
import logging
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from agents.code_generator import CodeGeneratorAgent
from utils.common import setup_logging

setup_logging("INFO")
logger = logging.getLogger("ParallelRepair")

class GitWorktreeManager:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.worktrees_dir = os.path.join(os.path.dirname(self.repo_path), "repair_worktrees")
        
    def setup(self):
        """确保主仓库干净且 worktrees 目录存在"""
        # 先清理 git worktree 记录
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo_path, check=False)
        
        if os.path.exists(self.worktrees_dir):
            shutil.rmtree(self.worktrees_dir)
        os.makedirs(self.worktrees_dir)
        
        # 再次清理，确保万无一失
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo_path, check=False)
        
        # 确保主仓库在干净状态
        subprocess.run(["git", "stash"], cwd=self.repo_path, check=False)
        
    def create_worktree(self, branch_name: str) -> str:
        """创建新的 worktree 和分支"""
        worktree_path = os.path.join(self.worktrees_dir, branch_name)
        
        # 检查分支是否存在
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=self.repo_path,
            capture_output=True
        )
        
        if result.returncode == 0:
            # 分支已存在，强制删除重建
            subprocess.run(["git", "branch", "-D", branch_name], cwd=self.repo_path, check=False)
            
        # 基于当前 HEAD 创建新分支
        cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path, "HEAD"]
        subprocess.run(cmd, cwd=self.repo_path, check=True)
        return worktree_path

    def merge_branch(self, branch_name: str) -> bool:
        """合并分支回主分支"""
        logger.info(f"正在合并分支 {branch_name}...")
        try:
            subprocess.run(["git", "merge", "--no-ff", branch_name], cwd=self.repo_path, check=True)
            return True
        except subprocess.CalledProcessError:
            logger.error(f"合并分支 {branch_name} 失败，可能存在冲突。请手动解决。")
            subprocess.run(["git", "merge", "--abort"], cwd=self.repo_path, check=False)
            return False

    def cleanup(self):
        """清理所有 worktree"""
        if os.path.exists(self.worktrees_dir):
            subprocess.run(["git", "worktree", "prune"], cwd=self.repo_path, check=False)
            shutil.rmtree(self.worktrees_dir, ignore_errors=True)

async def repair_single_target(worktree_path: str, test_file: str, branch_name: str, architecture: Dict[str, Any] | None = None, max_retries: int = 3):
    """在独立的 worktree 中修复单个测试文件"""
    logger.info(f"[{branch_name}] 开始修复: {test_file}")
    
    code_gen = CodeGeneratorAgent()
    
    # 1. 运行针对性测试
    # 注意：这里我们只跑这一个测试文件，速度极快
    cmd = ["pytest", test_file]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = worktree_path
    
    proc = await asyncio.create_subprocess_exec(
        *cmd, 
        cwd=worktree_path,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode == 0:
        logger.info(f"[{branch_name}] 测试已通过，无需修复")
        return True

    error_log = stdout.decode() + stderr.decode()
    
    # 2. 调用 LLM 修复
    # 我们复用 CodeGeneratorAgent.repair，但指定只修复相关文件
    # 注意：output_dir 必须指向 worktree_path
    logger.info(f"[{branch_name}] 检测到失败，正在调用 LLM 修复...")
    
    for attempt in range(max_retries):
        logger.info(f"[{branch_name}] 尝试修复 (第 {attempt+1}/{max_retries} 次)...")
        
        try:
            repair_result = await code_gen.repair(
                output_dir=worktree_path,
                error_log=error_log,
                max_files=2, # 限制每次只修2个文件，减少冲突
                architecture_design=architecture
            )
            
            if not repair_result.get("repaired"):
                logger.warning(f"[{branch_name}] LLM 无法修复 (Attempt {attempt+1})")
                # 如果是最后一次尝试，则失败
                if attempt == max_retries - 1:
                    return False
                # 否则继续下一次循环（可能需要重新运行测试以获取新错误）
            
            # 3. 验证修复
            proc_verify = await asyncio.create_subprocess_exec(
                *cmd, 
                cwd=worktree_path,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_v, stderr_v = await proc_verify.communicate()
            
            if proc_verify.returncode == 0:
                logger.info(f"[{branch_name}] 修复成功！")
                # 提交更改
                subprocess.run(["git", "add", "."], cwd=worktree_path, check=True)
                subprocess.run(["git", "commit", "-m", f"Fix: Auto-repair {test_file}"], cwd=worktree_path, check=True)
                return True
            else:
                verify_log = stdout_v.decode() + stderr_v.decode()
                logger.warning(f"[{branch_name}] 修复后验证仍失败 (Attempt {attempt+1})")
                logger.warning(f"验证日志: {verify_log[:500]}...")
                
                # 更新 error_log 为新的验证日志，供下一次修复使用
                error_log = verify_log
                
        except Exception as e:
            logger.error(f"[{branch_name}] 修复过程出错: {e}")
            return False

    return False

async def main():
    parser = argparse.ArgumentParser(description="基于 Git Worktree 的并行修复工具")
    parser.add_argument("--repo-dir", required=True, help="Git 仓库根目录 (包含 .git)")
    parser.add_argument("--arch-file", help="架构设计文件路径 (可选)")
    parser.add_argument("--limit", type=int, help="限制处理的测试文件数量 (用于调试)")
    parser.add_argument("--max-retries", type=int, default=3, help="每个文件的最大修复重试次数")
    parser.add_argument("--no-cleanup", action="store_true", help="保留 worktrees 用于调试")
    args = parser.parse_args()
    
    repo_dir = os.path.abspath(args.repo_dir)
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        logger.error(f"{repo_dir} 不是一个有效的 Git 仓库")
        return

    # 加载架构设计
    import json
    import glob
    architecture = None
    
    if args.arch_file:
        if os.path.exists(args.arch_file):
            with open(args.arch_file, 'r', encoding='utf-8') as f:
                architecture = json.load(f)
            logger.info(f"已加载架构设计: {args.arch_file}")
    else:
        # 尝试自动寻找
        # 假设结构: tests/output/development_execution_test/project_code -> tests/output/integration_test/
        parent_dir = os.path.dirname(repo_dir) # development_execution_test
        grand_parent = os.path.dirname(parent_dir) # output
        integration_dir = os.path.join(grand_parent, "integration_test")
        
        if os.path.exists(integration_dir):
            arch_files = sorted(glob.glob(os.path.join(integration_dir, "architecture_artifacts_*.json")), reverse=True)
            if arch_files:
                with open(arch_files[0], 'r', encoding='utf-8') as f:
                    architecture = json.load(f)
                logger.info(f"自动加载最新架构设计: {arch_files[0]}")

    git_manager = GitWorktreeManager(repo_dir)
    git_manager.setup()
    
    try:
        # 1. 全量扫描失败的测试
        logger.info("正在扫描失败的测试...")
        # 使用 --collect-only 或者是运行一次全量，这里为了准确，运行一次全量并解析输出
        # 为了演示，我们假设已经知道哪些文件失败，或者通过 pytest --lf (last failed) 获取
        # 这里简化为：查找 tests 目录下所有以 test_ 开头的文件，并发运行它们
        
        test_files = []
        tests_dir = os.path.join(repo_dir, "tests")
        if os.path.exists(tests_dir):
            for f in os.listdir(tests_dir):
                if f.startswith("test_") and f.endswith(".py"):
                    test_files.append(os.path.join("tests", f))
        
        if not test_files:
            logger.info("未找到测试文件")
            return

        if args.limit:
            test_files = test_files[:args.limit]
            logger.info(f"根据限制，仅处理前 {args.limit} 个文件")

        logger.info(f"找到 {len(test_files)} 个测试文件，准备并行验证与修复...")
        
        # 2. 并行分发任务
        tasks = []
        branches = []
        
        # 限制并发数，防止 LLM Rate Limit
        sem = asyncio.Semaphore(3) 
        
        async def worker(test_file):
            async with sem:
                branch_name = f"fix/{os.path.basename(test_file).replace('.py', '')}"
                worktree_path = git_manager.create_worktree(branch_name)
                branches.append(branch_name)
                
                success = await repair_single_target(worktree_path, test_file, branch_name, architecture, args.max_retries)
                return branch_name, success

        for tf in test_files:
            tasks.append(worker(tf))
            
        results = await asyncio.gather(*tasks)
        
        # 3. 合并结果
        logger.info("所有并行任务完成，开始合并...")
        success_count = 0
        for branch_name, success in results:
            if success:
                if git_manager.merge_branch(branch_name):
                    success_count += 1
            else:
                logger.warning(f"分支 {branch_name} 修复失败或验证未通过，跳过合并")
                
        logger.info(f"修复完成。成功合并 {success_count}/{len(test_files)} 个分支。")
        
    finally:
        if not args.no_cleanup:
            git_manager.cleanup()

if __name__ == "__main__":
    import argparse
    asyncio.run(main())
