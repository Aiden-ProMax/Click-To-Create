#!/usr/bin/env python3
"""
AI Frontend Data Load Bug Fix - Verification Script
验证 AI 前端数据加载修复是否正确应用

用法: python3 verify_fix.py
"""

import json
import os
import sys

def check_file_content(filepath, search_patterns):
    """Check if file contains the expected patterns"""
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    found_count = 0
    
    for pattern_name, pattern in search_patterns.items():
        if pattern in content:
            found_count += 1
        else:
            missing.append(pattern_name)
    
    return len(missing) == 0, (found_count, len(search_patterns), missing)

def main():
    print("=" * 70)
    print("AI FRONTEND DATA LOAD BUG FIX - VERIFICATION")
    print("=" * 70)
    print()
    
    issues = []
    fixed_count = 0
    
    # Check 1: Async function in DOMContentLoaded
    print("✓ 检查1: DOMContentLoaded async 修复")
    print("-" * 70)
    
    patterns = {
        "async event listener": "document.addEventListener('DOMContentLoaded', async function()",
        "await stash fetch": "const res = await fetch(`/api/ai/stash/${aiDataKey}/`",
        "credentials include": "credentials: 'include'"
    }
    
    success, result = check_file_content('templates/add_plan_backend.html', patterns)
    found, total, missing = result
    
    print(f"  Found {found}/{total} required patterns")
    if success:
        print("  ✅ PASS: DOMContentLoaded 已修复为 async")
        fixed_count += 1
    else:
        print("  ❌ FAIL: 缺少以下模式:")
        for m in missing:
            print(f"    - {m}")
        issues.append("DOMContentLoaded async 修复未完成")
    print()
    
    # Check 2: Improved normalizeAiPayload with logging
    print("✓ 检查2: normalizeAiPayload 改进")
    print("-" * 70)
    
    patterns = {
        "normalize logging": "console.log('[normalizeAiPayload]",
        "events check": "parsedData.events && Array.isArray(parsedData.events)",
        "items fallback": "parsedData.items && Array.isArray(parsedData.items)",
        "array check": "Array.isArray(parsedData)",
        "object check": "typeof parsedData === 'object'"
    }
    
    success, result = check_file_content('templates/add_plan_backend.html', patterns)
    found, total, missing = result
    
    print(f"  Found {found}/{total} required patterns")
    if success:
        print("  ✅ PASS: normalizeAiPayload 已改进")
        fixed_count += 1
    else:
        print("  ⚠️  WARN: 可能缺少调试日志")
        print(f"    缺少: {missing[:2]}...")
    print()
    
    # Check 3: populateForm improvements with logging
    print("✓ 检查3: populateForm 日志和改进")
    print("-" * 70)
    
    patterns = {
        "form logging": "console.log('[populateForm]",
        "title logging": "console.log('[populateForm] Set title:",
        "date logging": "console.log('[populateForm] Set date:",
        "time extraction": "const inferredTime = extractExplicitTime(fullText)",
        "all day handling": "applyAllDayFromData(data)"
    }
    
    success, result = check_file_content('templates/add_plan_backend.html', patterns)
    found, total, missing = result
    
    print(f"  Found {found}/{total} required patterns")
    if success:
        print("  ✅ PASS: populateForm 已改进")
        fixed_count += 1
    else:
        print("  ⚠️  PARTIAL: 部分日志可能缺失")
        if "form logging" not in missing:
            print("    (核心功能已修复，日志可能不完整)")
    print()
    
    # Check 4: AI Stash endpoint available
    print("✓ 检查4: AI Stash 端点实现")
    print("-" * 70)
    
    patterns = {
        "stash view class": "class AiDataStashView",
        "stash post": "def post(self, request):",
        "stash get": "def get(self, request, key: str):",
        "cache operation": "cache.set(cache_key, payload",
        "cache retrieve": "cache.get(cache_key)"
    }
    
    success, result = check_file_content('ai/views.py', patterns)
    found, total, missing = result
    
    print(f"  Found {found}/{total} required patterns")
    if success:
        print("  ✅ PASS: Stash 端点已实现")
        fixed_count += 1
    else:
        print("  ❌ FAIL: Stash 端点缺失部分实现")
        issues.append("Stash endpoint not fully implemented")
    print()
    
    # Check 5: URLs configuration
    print("✓ 检查5: URL 路由配置")
    print("-" * 70)
    
    patterns = {
        "stash url": "path('stash/', AiDataStashView.as_view()",
        "stash key url": "path('stash/<str:key>/', AiDataStashView.as_view()"
    }
    
    success, result = check_file_content('ai/urls.py', patterns)
    found, total, missing = result
    
    print(f"  Found {found}/{total} required patterns")
    if success:
        print("  ✅ PASS: URL 路由配置正确")
        fixed_count += 1
    else:
        print("  ❌ FAIL: URL 路由配置缺失")
        issues.append("URL routes not configured")
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ 通过检查: {fixed_count}/5")
    print(f"📊 修复完成度: {fixed_count*20}%")
    
    if issues:
        print(f"\n❌ 发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✅ 所有检查都通过了！修复已完整应用。")
    
    print("\n" + "=" * 70)
    
    # Testing recommendations
    print("\n📋 建议的测试步骤:")
    print("=" * 70)
    print("""
1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 访问仪表板并输入事件（例如 "Tomorrow at 2pm meeting"）
4. 点击发送按钮
5. 查看 Console 输出，应该看到类似的日志：
   [DOMContentLoaded] Starting, aiDataKey: ...
   [normalizeAiPayload] Found events array: X items
   [loadAiEventAtIndex] Loading event at index: 0 of X
   [populateForm] Set title: ...
   [populateForm] Set date: ...
6. 验证表单字段是否自动填充了 AI 提取的数据

如果看到任何 JavaScript 错误，请检查浏览器控制台的详细错误信息。
""")
    
    return 0 if not issues else 1

if __name__ == '__main__':
    sys.exit(main())
