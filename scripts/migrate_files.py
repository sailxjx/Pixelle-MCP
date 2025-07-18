#!/usr/bin/env python3
"""
文件迁移脚本
从 MinIO HTTP API 下载文件并迁移到 mcp-base 的本地存储
"""

import os
import sys
import requests
from pathlib import Path
from typing import List, Tuple


def get_project_root() -> Path:
    """获取项目根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent


def scan_minio_files(minio_dir: Path, minio_base_url: str) -> List[Tuple[str, str]]:
    """
    扫描 MinIO 目录获取文件名，并构造下载URL
    
    Args:
        minio_dir: MinIO 本地目录（用于扫描文件夹名）
        minio_base_url: MinIO HTTP 基础URL
        
    Returns:
        List[Tuple[str, str]]: [(下载URL, 本地文件名), ...]
        
    Note:
        MinIO存储机制：xxx.png文件会以xxx.png文件夹形式存在，
        真实内容通过 http://host/files/xxx.png 访问
    """
    files = []
    
    if not minio_dir.exists():
        print(f"❌ MinIO 目录不存在: {minio_dir}")
        return files
    
    print(f"📁 扫描 MinIO 目录: {minio_dir}")
    print(f"🌐 MinIO 基础URL: {minio_base_url}")
    
    # 只遍历一级子文件夹，文件夹名即为文件ID
    for item in minio_dir.iterdir():
        if item.is_dir():
            # 文件夹名就是文件ID/文件名
            file_id = item.name
            
            # 构造下载URL
            download_url = f"{minio_base_url.rstrip('/')}/files/{file_id}"
            files.append((download_url, file_id))
            print(f"  📄 发现文件: {file_id}")
            print(f"      📥 下载URL: {download_url}")
    
    print(f"✅ 共发现 {len(files)} 个文件")
    return files


def migrate_files(files: List[Tuple[str, str]], target_dir: Path, dry_run: bool = False) -> Tuple[int, int]:
    """
    从MinIO HTTP API下载文件到目标目录
    
    Args:
        files: 文件列表 [(下载URL, 目标文件名), ...]
        target_dir: 目标目录
        dry_run: 是否为试运行（不实际下载文件）
        
    Returns:
        Tuple[int, int]: (成功数量, 失败数量)
    """
    success_count = 0
    error_count = 0
    
    # 确保目标目录存在
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 目标目录: {target_dir}")
    else:
        print(f"🧪 试运行模式 - 目标目录: {target_dir}")
    
    print(f"🚀 开始迁移 {len(files)} 个文件...")
    print("-" * 60)
    
    for i, (download_url, target_filename) in enumerate(files, 1):
        target_path = target_dir / target_filename
        
        try:
            if dry_run:
                print(f"[{i:2d}/{len(files)}] 🧪 试运行: {download_url} -> {target_filename}")
                if target_path.exists():
                    print(f"           ⚠️  目标文件已存在: {target_path}")
            else:
                print(f"[{i:2d}/{len(files)}] 📥 下载: {target_filename}")
                print(f"           🔗 URL: {download_url}")
                
                # 检查目标文件是否已存在
                if target_path.exists():
                    print(f"           ⚠️  目标文件已存在，跳过: {target_path}")
                    success_count += 1
                    continue
                
                # 下载文件
                response = requests.get(download_url, timeout=30)
                response.raise_for_status()
                
                # 保存文件
                with open(target_path, 'wb') as f:
                    f.write(response.content)
                
                # 验证下载结果
                if target_path.exists() and target_path.stat().st_size > 0:
                    print(f"           ✅ 下载成功: {target_path.stat().st_size} bytes")
                    success_count += 1
                else:
                    print(f"           ❌ 下载验证失败")
                    error_count += 1
                    
        except requests.RequestException as e:
            print(f"           ❌ 下载失败: {e}")
            error_count += 1
        except Exception as e:
            print(f"           ❌ 处理失败: {e}")
            error_count += 1
    
    print("-" * 60)
    print(f"📊 迁移完成: 成功 {success_count} 个, 失败 {error_count} 个")
    
    return success_count, error_count


def test_specific_file(filename: str, minio_base_url: str, target_dir: Path):
    """测试特定文件的迁移"""
    print(f"🧪 测试文件迁移: {filename}")
    
    # 直接构造下载URL和文件名
    download_url = f"{minio_base_url.rstrip('/')}/files/{filename}"
    found_files = [(download_url, filename)]
    
    print(f"✅ 准备下载文件:")
    for download_url, target_filename in found_files:
        print(f"  📄 {download_url} -> {target_filename}")
    
    # 执行迁移
    success_count, error_count = migrate_files(found_files, target_dir, dry_run=False)
    
    return error_count == 0


def main():
    """主函数"""
    print("🎯 Pixelle MCP 文件迁移工具")
    print("=" * 60)
    
    # 获取路径和配置
    project_root = get_project_root()
    minio_dir = project_root / "mcp-server" / "data" / "minio" / "files"
    target_dir = project_root / "mcp-base" / "data" / "files"
    minio_base_url = "http://30.150.44.149:9000"  # MinIO HTTP 访问地址
    
    print(f"📁 项目根目录: {project_root}")
    print(f"📁 MinIO 目录: {minio_dir}")
    print(f"📁 目标目录: {target_dir}")
    print(f"🌐 MinIO URL: {minio_base_url}")
    print()
    
    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # 测试特定文件
            test_filename = "c6958285476b486da0e5916864ad801e.png"
            if len(sys.argv) > 2:
                test_filename = sys.argv[2]
            
            success = test_specific_file(test_filename, minio_base_url, target_dir)
            sys.exit(0 if success else 1)
        
        elif sys.argv[1] == "--dry-run":
            # 试运行模式
            files = scan_minio_files(minio_dir, minio_base_url)
            if files:
                migrate_files(files, target_dir, dry_run=True)
            sys.exit(0)
        
        elif sys.argv[1] == "--help":
            print("用法:")
            print("  python migrate_files.py                    # 执行完整迁移")
            print("  python migrate_files.py --test [filename]  # 测试特定文件")
            print("  python migrate_files.py --dry-run          # 试运行模式")
            print("  python migrate_files.py --help             # 显示帮助")
            sys.exit(0)
    
    # 扫描文件
    files = scan_minio_files(minio_dir, minio_base_url)
    
    if not files:
        print("❌ 没有找到需要迁移的文件")
        sys.exit(1)
    
    # 询问用户确认
    print()
    print(f"❓ 即将迁移 {len(files)} 个文件到 {target_dir}")
    print("   这将从MinIO下载文件到本地存储")
    
    confirm = input("是否继续? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 用户取消迁移")
        sys.exit(0)
    
    # 执行迁移
    success_count, error_count = migrate_files(files, target_dir, dry_run=False)
    
    # 显示结果
    print()
    if error_count == 0:
        print("🎉 迁移完成！所有文件已成功下载到本地存储")
    else:
        print(f"⚠️  迁移完成，但有 {error_count} 个文件失败")
        sys.exit(1)


if __name__ == "__main__":
    main() 