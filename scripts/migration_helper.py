#!/usr/bin/env python3
"""
前端代码迁移辅助脚本
帮助快速识别需要迁移的代码模式
"""
import re
import sys
from pathlib import Path


def find_dify_patterns(file_path):
    """查找文件中的 Dify API 直接调用模式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    patterns = {
        'api_key': r'apiKey:\s*["\']app-[a-zA-Z0-9]+["\']',
        'base_url': r'baseUrl:\s*["\']http[s]?://[^"\']+["\']',
        'fetch_upload': r'fetch\([^)]*files/upload',
        'fetch_workflow': r'fetch\([^)]*workflows/run',
        'authorization': r'Authorization:\s*[`"\']Bearer\s+\$\{[^}]+\}[`"\']',
    }

    findings = []
    for pattern_name, pattern in patterns.items():
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            findings.append({
                'type': pattern_name,
                'line': line_num,
                'text': match.group(0)
            })

    return findings


def main():
    if len(sys.argv) < 2:
        print("用法: python migration_helper.py <js文件路径>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"错误: 文件不存在: {file_path}")
        sys.exit(1)

    print(f"\n🔍 分析文件: {file_path}\n")

    findings = find_dify_patterns(file_path)

    if not findings:
        print("✅ 未发现需要迁移的 Dify API 调用模式")
        return

    print(f"⚠️  发现 {len(findings)} 处需要迁移的代码:\n")

    for finding in findings:
        print(f"  行 {finding['line']:4d} | {finding['type']:20s} | {finding['text'][:60]}")

    print("\n📖 迁移建议:")
    print("  1. 移除 DIFY_CONFIG 配置对象")
    print("  2. 使用 DifyProxyClient.uploadFile() 替代文件上传")
    print("  3. 使用 DifyProxyClient.runWorkflow() 替代工作流调用")
    print("  4. 使用 DifyProxyClient.runWorkflowStream() 替代流式调用")
    print("\n详细文档: docs/dify_proxy_migration.md\n")


if __name__ == "__main__":
    main()
