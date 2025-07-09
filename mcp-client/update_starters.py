#!/usr/bin/env python3
"""
批量更新starter文件，为首条用户消息添加\u200B前缀标识
"""

import json
import os
from pathlib import Path

def update_starter_file(file_path: Path) -> bool:
    """更新单个starter文件"""
    try:
        # 读取原文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查messages字段
        if 'messages' not in data or not isinstance(data['messages'], list):
            print(f"跳过 {file_path.name}：没有messages字段或格式不正确")
            return False
        
        # 查找首条用户消息
        first_user_msg = None
        for msg in data['messages']:
            if (isinstance(msg, dict) and 
                msg.get('role') == 'user' and 
                msg.get('type') == 'message'):
                first_user_msg = msg
                break
        
        if not first_user_msg:
            print(f"跳过 {file_path.name}：没有找到用户消息")
            return False
        
        content = first_user_msg.get('content', '')
        if not content:
            print(f"跳过 {file_path.name}：用户消息内容为空")
            return False
        
        # 检查是否已经有\u200B前缀
        if content.startswith('\u200B'):
            print(f"跳过 {file_path.name}：已经有\u200B前缀")
            return False
        
        # 添加\u200B前缀
        first_user_msg['content'] = '\u200B' + content
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 更新成功: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ 更新失败 {file_path.name}: {e}")
        return False

def main():
    """主函数"""
    # 定义要处理的目录
    starters_dirs = [
        Path("./starters"),  # 系统预置目录
        Path("./data/custom_starters")  # 用户自定义目录
    ]
    
    total_files = 0
    updated_files = 0
    
    for starters_dir in starters_dirs:
        if not starters_dir.exists():
            print(f"目录不存在，跳过: {starters_dir}")
            continue
        
        print(f"\n处理目录: {starters_dir}")
        print("-" * 50)
        
        # 遍历所有.json文件
        for json_file in starters_dir.glob("*.json"):
            total_files += 1
            if update_starter_file(json_file):
                updated_files += 1
    
    print("\n" + "=" * 50)
    print(f"批量更新完成！")
    print(f"总文件数: {total_files}")
    print(f"更新文件数: {updated_files}")
    print(f"跳过文件数: {total_files - updated_files}")

if __name__ == "__main__":
    main() 