#!/bin/bash

# 批量更新starter文件脚本
# 为所有现有starter文件的首条用户消息添加\u200B前缀标识

echo "开始批量更新starter文件..."
echo "此脚本将为所有现有starter文件的首条用户消息添加\\u200B前缀标识"
echo ""

# 检查Python脚本是否存在
if [ ! -f "update_starters.py" ]; then
    echo "错误：找不到update_starters.py文件"
    exit 1
fi

# 执行Python更新脚本
python3 update_starters.py

echo ""
echo "批量更新完成！"
echo "现在新保存的starter消息将自动添加\\u200B前缀，用于区分starter和真实用户输入。" 