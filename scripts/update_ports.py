#!/usr/bin/env python3
"""
端口更新脚本
将 JSON 文件中的 MinIO 端口 :9000 更新为 mcp-base 端口 :9001
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Tuple


def get_project_root() -> Path:
    """获取项目根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent


def scan_json_files(directories: List[Path]) -> List[Path]:
    """
    扫描目录中的所有JSON文件
    
    Args:
        directories: 要扫描的目录列表
        
    Returns:
        List[Path]: JSON文件路径列表
    """
    json_files = []
    
    for directory in directories:
        if not directory.exists():
            print(f"⚠️  目录不存在: {directory}")
            continue
            
        print(f"📁 扫描目录: {directory}")
        
        # 查找所有JSON文件
        for json_file in directory.rglob("*.json"):
            if json_file.is_file():
                json_files.append(json_file)
                print(f"  📄 发现文件: {json_file.name}")
    
    print(f"✅ 共发现 {len(json_files)} 个JSON文件")
    return json_files


def backup_file(file_path: Path) -> Path:
    """
    备份文件
    
    Args:
        file_path: 原文件路径
        
    Returns:
        Path: 备份文件路径
    """
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_json_file(file_path: Path, old_port: str, new_port: str, dry_run: bool = False) -> Tuple[bool, int]:
    """
    更新JSON文件中的端口配置
    
    Args:
        file_path: JSON文件路径
        old_port: 旧端口（如 ':9000'）
        new_port: 新端口（如 ':9001'）
        dry_run: 是否为试运行
        
    Returns:
        Tuple[bool, int]: (是否有更改, 替换次数)
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含要替换的内容
        if old_port not in content:
            return False, 0
        
        # 执行替换
        new_content = content.replace(old_port, new_port)
        replace_count = content.count(old_port)
        
        if dry_run:
            print(f"    🧪 试运行: 将替换 {replace_count} 处 '{old_port}' -> '{new_port}'")
            return True, replace_count
        
        # 创建备份
        backup_path = backup_file(file_path)
        print(f"    💾 备份文件: {backup_path.name}")
        
        # 写入更新后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"    ✅ 替换成功: {replace_count} 处 '{old_port}' -> '{new_port}'")
        return True, replace_count
        
    except json.JSONDecodeError as e:
        print(f"    ❌ JSON格式错误: {e}")
        return False, 0
    except Exception as e:
        print(f"    ❌ 处理失败: {e}")
        return False, 0


def update_files(json_files: List[Path], old_port: str, new_port: str, dry_run: bool = False) -> Tuple[int, int, int]:
    """
    批量更新文件
    
    Args:
        json_files: JSON文件列表
        old_port: 旧端口
        new_port: 新端口
        dry_run: 是否为试运行
        
    Returns:
        Tuple[int, int, int]: (更新文件数, 跳过文件数, 总替换次数)
    """
    updated_count = 0
    skipped_count = 0
    total_replacements = 0
    
    print(f"🚀 开始更新 {len(json_files)} 个JSON文件...")
    print(f"🔄 替换规则: '{old_port}' -> '{new_port}'")
    if dry_run:
        print("🧪 试运行模式 - 不会实际修改文件")
    print("-" * 60)
    
    for i, json_file in enumerate(json_files, 1):
        print(f"[{i:2d}/{len(json_files)}] 📄 处理: {json_file.name}")
        
        has_changes, replace_count = update_json_file(json_file, old_port, new_port, dry_run)
        
        if has_changes:
            updated_count += 1
            total_replacements += replace_count
        else:
            skipped_count += 1
            print(f"    ⏭️  跳过: 未找到 '{old_port}'")
    
    print("-" * 60)
    print(f"📊 更新完成:")
    print(f"   📝 更新文件: {updated_count} 个")
    print(f"   ⏭️  跳过文件: {skipped_count} 个")
    print(f"   🔄 总替换次数: {total_replacements} 处")
    
    return updated_count, skipped_count, total_replacements


def restore_backups(directories: List[Path]):
    """恢复所有备份文件"""
    print("🔄 恢复备份文件...")
    
    restored_count = 0
    for directory in directories:
        if not directory.exists():
            continue
            
        # 查找所有备份文件
        for backup_file in directory.rglob("*.json.bak"):
            if backup_file.is_file():
                original_file = backup_file.with_suffix("")  # 去掉.bak后缀
                
                try:
                    shutil.copy2(backup_file, original_file)
                    backup_file.unlink()  # 删除备份文件
                    print(f"  ✅ 恢复: {original_file.name}")
                    restored_count += 1
                except Exception as e:
                    print(f"  ❌ 恢复失败 {original_file.name}: {e}")
    
    print(f"📊 恢复完成: {restored_count} 个文件")


def cleanup_backups(directories: List[Path]):
    """清理备份文件"""
    print("🧹 清理备份文件...")
    
    cleaned_count = 0
    for directory in directories:
        if not directory.exists():
            continue
            
        # 查找所有备份文件
        for backup_file in directory.rglob("*.json.bak"):
            if backup_file.is_file():
                try:
                    backup_file.unlink()
                    print(f"  🗑️  删除备份: {backup_file.name}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"  ❌ 删除失败 {backup_file.name}: {e}")
    
    print(f"📊 清理完成: {cleaned_count} 个备份文件")


def main():
    """主函数"""
    print("🎯 Pixelle MCP 端口更新工具")
    print("=" * 60)
    
    # 获取目录路径
    project_root = get_project_root()
    directories = [
        project_root / "mcp-client" / "starters",
        project_root / "mcp-client" / "data" / "custom_starters",
        project_root / "mcp-server" / "data" / "custom_workflows"
    ]
    
    print(f"📁 项目根目录: {project_root}")
    for directory in directories:
        print(f"📁 扫描目录: {directory}")
    print()
    
    # 端口配置
    old_port = ":9000"
    new_port = ":9001"
    
    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            # 试运行模式
            print("🧪 试运行模式 - 查看将要进行的更改")
            json_files = scan_json_files(directories)
            if json_files:
                update_files(json_files, old_port, new_port, dry_run=True)
            sys.exit(0)
        
        elif sys.argv[1] == "--restore":
            # 恢复备份
            restore_backups(directories)
            sys.exit(0)
        
        elif sys.argv[1] == "--cleanup":
            # 清理备份
            cleanup_backups(directories)
            sys.exit(0)
        
        elif sys.argv[1] == "--help":
            print("用法:")
            print("  python update_ports.py                # 执行端口更新")
            print("  python update_ports.py --dry-run      # 试运行模式")
            print("  python update_ports.py --restore      # 恢复备份文件")
            print("  python update_ports.py --cleanup      # 清理备份文件")
            print("  python update_ports.py --help         # 显示帮助")
            print()
            print("功能:")
            print(f"  将JSON文件中的 '{old_port}' 替换为 '{new_port}'")
            print("  自动备份原文件（.bak后缀）")
            print("  支持批量处理和错误恢复")
            sys.exit(0)
    
    # 扫描JSON文件
    json_files = scan_json_files(directories)
    
    if not json_files:
        print("❌ 没有找到需要更新的JSON文件")
        sys.exit(1)
    
    # 询问用户确认
    print()
    print(f"❓ 即将更新 {len(json_files)} 个JSON文件")
    print(f"   将 '{old_port}' 替换为 '{new_port}'")
    print("   原文件将自动备份（.bak后缀）")
    
    confirm = input("是否继续? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 用户取消更新")
        sys.exit(0)
    
    # 执行更新
    updated_count, skipped_count, total_replacements = update_files(
        json_files, old_port, new_port, dry_run=False
    )
    
    # 显示结果
    print()
    if updated_count > 0:
        print("🎉 端口更新完成！")
        print(f"   📝 更新了 {updated_count} 个文件")
        print(f"   🔄 总共替换了 {total_replacements} 处")
        print()
        print("💡 提示:")
        print("   - 原文件已备份为 .bak 文件")
        print("   - 如需恢复: python update_ports.py --restore")
        print("   - 如需清理备份: python update_ports.py --cleanup")
    else:
        print("ℹ️  没有找到需要更新的内容")


if __name__ == "__main__":
    main() 