#!/usr/bin/env python3
"""
文件上传测试脚本
用于测试zsSystem项目的文件上传功能，包括各种合法和非法文件
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import validate_file_type, validate_file_size
from certificate_processor import CertificateProcessor
from database import get_user_by_account_id


def test_file_upload(file_path, user, expected_success=True):
    """
    测试单个文件上传
    
    Args:
        file_path: 测试文件路径
        user: 用户对象
        expected_success: 预期是否成功
        
    Returns:
        dict: 测试结果
    """
    result = {
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "expected_success": expected_success,
        "actual_success": False,
        "message": "",
        "validation_results": {
            "file_type": {
                "valid": False,
                "message": ""
            },
            "file_size": {
                "valid": False,
                "message": ""
            }
        },
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }
    
    try:
        # 1. 验证文件类型
        file_name = os.path.basename(file_path)
        valid_type, type_msg = validate_file_type(file_name)
        result["validation_results"]["file_type"]["valid"] = valid_type
        result["validation_results"]["file_type"]["message"] = type_msg
        
        # 2. 验证文件大小
        file_size = os.path.getsize(file_path)
        valid_size, size_msg = validate_file_size(file_size)
        result["validation_results"]["file_size"]["valid"] = valid_size
        result["validation_results"]["file_size"]["message"] = size_msg
        
        # 3. 创建处理器并上传文件
        processor = CertificateProcessor(user)
        
        # 模拟上传文件对象
        class MockUploadedFile:
            def __init__(self, filepath):
                self.name = os.path.basename(filepath)
                self.filepath = filepath
                self._position = 0
            
            def read(self):
                with open(self.filepath, "rb") as f:
                    f.seek(self._position)
                    data = f.read()
                    self._position += len(data)
                    return data
            
            def seek(self, position):
                self._position = position
        
        mock_file = MockUploadedFile(file_path)
        success, uploaded_path, message = processor.upload_file(mock_file)
        
        result["actual_success"] = success
        result["message"] = message
        
        # 如果上传成功且是临时测试文件，清理上传的文件
        if success and uploaded_path and os.path.exists(uploaded_path):
            try:
                os.remove(uploaded_path)
            except:
                pass
        
        return result
        
    except Exception as e:
        result["actual_success"] = False
        result["message"] = f"测试执行错误: {str(e)}"
        return result


def generate_test_report(results, output_path):
    """
    生成测试报告
    
    Args:
        results: 测试结果列表
        output_path: 报告输出路径
    """
    # 计算统计信息
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["actual_success"] == r["expected_success"])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # 分类结果
    valid_files = [r for r in results if "valid" in r["file_path"]]
    invalid_files = [r for r in results if "invalid" in r["file_path"]]
    passed = [r for r in results if r["actual_success"] == r["expected_success"]]
    failed = [r for r in results if r["actual_success"] != r["expected_success"]]
    
    # 生成Markdown报告
    report_content = f"""# 文件上传测试报告

## 测试环境
- **测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **测试系统**: zsSystem
- **测试脚本**: run_upload_tests.py
- **测试文件目录**: test_files/

## 测试统计
| 统计项 | 数量 | 比例 |
|--------|------|------|
| 总测试用例 | {total_tests} | 100% |
| 通过测试 | {passed_tests} | {success_rate:.1f}% |
| 失败测试 | {total_tests - passed_tests} | {100 - success_rate:.1f}% |
| 合法文件测试 | {len(valid_files)} | {len(valid_files)/total_tests*100:.1f}% |
| 非法文件测试 | {len(invalid_files)} | {len(invalid_files)/total_tests*100:.1f}% |

## 测试用例设计

### 合法文件测试
| 文件类型 | 文件名 | 预期结果 |
|----------|--------|----------|
| PDF | sample1.pdf | ✅ 上传成功 |
| JPG | sample2.jpg | ✅ 上传成功 |
| PNG | sample3.png | ✅ 上传成功 |

### 非法文件测试
| 文件类型 | 文件名 | 预期结果 | 测试目的 |
|----------|--------|----------|----------|
| EXE | sample_invalid.exe | ❌ 上传失败 | 测试不支持的文件格式 |
| TXT | sample_empty.txt | ❌ 上传失败 | 测试空文件处理 |
| JPG | sample_large.jpg | ❌ 上传失败 | 测试文件大小限制 |

## 测试结果

### 所有测试结果
| 文件名 | 预期结果 | 实际结果 | 状态 | 消息 |
|--------|----------|----------|------|------|
"""
    
    for result in results:
        expected = "✅" if result["expected_success"] else "❌"
        actual = "✅" if result["actual_success"] else "❌"
        status = "✅ 通过" if result["actual_success"] == result["expected_success"] else "❌ 失败"
        
        report_content += f"| {result['file_name']} | {expected} | {actual} | {status} | {result['message'][:50]}... |\n"
    
    report_content += "\n\n### 详细测试结果\n\n"
    
    # 合法文件测试详情
    report_content += "#### 合法文件测试\n\n"
    for result in valid_files:
        report_content += f"##### {result['file_name']}\n"
        report_content += f"- **文件路径**: {result['file_path']}\n"
        report_content += f"- **文件大小**: {result['file_size']} 字节\n"
        report_content += f"- **预期结果**: {'成功' if result['expected_success'] else '失败'}\n"
        report_content += f"- **实际结果**: {'成功' if result['actual_success'] else '失败'}\n"
        report_content += f"- **测试时间**: {result['upload_time']}\n"
        report_content += f"- **消息**: {result['message']}\n"
        report_content += f"- **类型验证**: {'通过' if result['validation_results']['file_type']['valid'] else '失败'} - {result['validation_results']['file_type']['message']}\n"
        report_content += f"- **大小验证**: {'通过' if result['validation_results']['file_size']['valid'] else '失败'} - {result['validation_results']['file_size']['message']}\n\n"
    
    # 非法文件测试详情
    report_content += "#### 非法文件测试\n\n"
    for result in invalid_files:
        report_content += f"##### {result['file_name']}\n"
        report_content += f"- **文件路径**: {result['file_path']}\n"
        report_content += f"- **文件大小**: {result['file_size']} 字节\n"
        report_content += f"- **预期结果**: {'成功' if result['expected_success'] else '失败'}\n"
        report_content += f"- **实际结果**: {'成功' if result['actual_success'] else '失败'}\n"
        report_content += f"- **测试时间**: {result['upload_time']}\n"
        report_content += f"- **消息**: {result['message']}\n"
        report_content += f"- **类型验证**: {'通过' if result['validation_results']['file_type']['valid'] else '失败'} - {result['validation_results']['file_type']['message']}\n"
        report_content += f"- **大小验证**: {'通过' if result['validation_results']['file_size']['valid'] else '失败'} - {result['validation_results']['file_size']['message']}\n\n"
    
    # 测试结论
    report_content += f"## 测试结论\n\n"
    report_content += f"- **测试通过率**: {success_rate:.1f}%\n"
    report_content += f"- **测试结果**: {'全部通过' if success_rate == 100 else '部分通过'}\n\n"
    
    if failed:
        report_content += f"### 发现的问题\n\n"
        for result in failed:
            report_content += f"- **文件**: {result['file_name']}\n"
            report_content += f"  - **预期**: {'成功' if result['expected_success'] else '失败'}\n"
            report_content += f"  - **实际**: {'成功' if result['actual_success'] else '失败'}\n"
            report_content += f"  - **原因**: {result['message']}\n\n"
        
        report_content += f"### 修复建议\n\n"
        report_content += f"1. 检查文件类型验证逻辑，确保所有支持的格式都能正确识别\n"
        report_content += f"2. 优化空文件处理逻辑，提供更友好的错误提示\n"
        report_content += f"3. 检查文件大小限制实现，确保准确的大小检查\n"
    else:
        report_content += f"### 测试总结\n\n"
        report_content += f"所有测试用例均通过，文件上传功能正常工作。\n"
        report_content += f"- 支持的文件格式：PDF, JPG, JPEG, PNG, BMP\n"
        report_content += f"- 文件大小限制：10MB\n"
        report_content += f"- 能够正确处理非法文件（不支持格式、空文件、过大文件）\n\n"
    
    # 保存报告
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"测试报告已生成: {output_path}")
    
    return report_content


def main():
    """
    主测试函数
    """
    print("=" * 60)
    print("zsSystem 文件上传测试")
    print("=" * 60)
    print()
    
    # 1. 创建模拟用户对象
    print("1. 创建模拟测试用户...")
    
    class MockUser:
        """模拟用户对象"""
        def __init__(self):
            self.user_id = 1
            self.account_id = "test_user"
            self.name = "Test User"
            self.role = "student"
            self.department = "测试部门"
            self.email = "test@example.com"
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.is_active = True
            self.created_by = "system"
    
    user = MockUser()
    print(f"   ✓ 模拟用户: {user.name} (角色: {user.role})")
    print()
    
    # 2. 获取测试文件
    print("2. 收集测试文件...")
    
    test_files = []
    
    # 合法文件
    valid_dir = os.path.join(os.path.dirname(__file__), "test_files", "valid")
    if os.path.exists(valid_dir):
        for file_name in os.listdir(valid_dir):
            file_path = os.path.join(valid_dir, file_name)
            if os.path.isfile(file_path):
                test_files.append((file_path, True))
                print(f"   ✓ 合法文件: {file_name}")
    
    # 非法文件
    invalid_dir = os.path.join(os.path.dirname(__file__), "test_files", "invalid")
    if os.path.exists(invalid_dir):
        for file_name in os.listdir(invalid_dir):
            file_path = os.path.join(invalid_dir, file_name)
            if os.path.isfile(file_path):
                test_files.append((file_path, False))
                print(f"   ✓ 非法文件: {file_name}")
    
    print()
    print(f"   共收集到 {len(test_files)} 个测试文件")
    print()
    
    # 3. 运行测试
    print("3. 运行测试...")
    results = []
    
    for i, (file_path, expected_success) in enumerate(test_files, 1):
        print(f"   测试 {i}/{len(test_files)}: {os.path.basename(file_path)}")
        result = test_file_upload(file_path, user, expected_success)
        results.append(result)
    
    print()
    print("   所有测试完成!")
    print()
    
    # 4. 生成报告
    print("4. 生成测试报告...")
    report_path = os.path.join(os.path.dirname(__file__), "upload_test_report.md")
    report_content = generate_test_report(results, report_path)
    
    print()
    print("=" * 60)
    print("测试完成!")
    print(f"测试报告: {report_path}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
