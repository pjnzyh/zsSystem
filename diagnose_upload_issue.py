"""
诊断文件上传问题
分析"文件保存失败"错误的根本原因
"""
import os
import sys
import stat

sys.path.insert(0, os.path.dirname(__file__))


def check_directory_permissions():
    """检查目录权限"""
    print("="*60)
    print("1. 检查目录权限")
    print("="*60 + "\n")
    
    base_dir = "uploads"
    current_dir = os.getcwd()
    
    print(f"当前工作目录: {current_dir}")
    print(f"目标上传目录: {base_dir}\n")
    
    # 检查基础目录
    if os.path.exists(base_dir):
        print(f"✓ 基础目录存在: {os.path.abspath(base_dir)}")
        
        # 检查权限
        try:
            test_file = os.path.join(base_dir, "test_permission.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"✓ 目录可写\n")
        except PermissionError:
            print(f"✗ 目录无写入权限！\n")
            return False
        except Exception as e:
            print(f"✗ 写入测试失败: {str(e)}\n")
            return False
    else:
        print(f"⚠ 基础目录不存在，尝试创建...\n")
        try:
            os.makedirs(base_dir)
            print(f"✓ 目录创建成功: {os.path.abspath(base_dir)}\n")
        except Exception as e:
            print(f"✗ 目录创建失败: {str(e)}\n")
            return False
    
    return True


def test_create_upload_dir():
    """测试创建上传目录功能"""
    print("="*60)
    print("2. 测试创建上传目录")
    print("="*60 + "\n")
    
    try:
        from utils import create_upload_dir
        
        upload_dir = create_upload_dir()
        print(f"✓ 上传目录创建成功")
        print(f"  相对路径: {upload_dir}")
        print(f"  绝对路径: {os.path.abspath(upload_dir)}")
        print(f"  目录存在: {os.path.exists(upload_dir)}\n")
        
        # 检查是否可写
        test_file = os.path.join(upload_dir, "test.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"✓ 文件写入测试成功")
            print(f"  测试文件: {test_file}")
            print(f"  文件大小: {file_size} 字节\n")
            os.remove(test_file)
            return True
        else:
            print(f"✗ 文件写入后不存在\n")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_file_save_process():
    """测试完整的文件保存流程"""
    print("="*60)
    print("3. 测试完整文件保存流程")
    print("="*60 + "\n")
    
    try:
        from utils import create_upload_dir, generate_unique_filename
        import shutil
        
        # 使用测试图片
        test_image = r"d:\hello_ai\1.jpg"
        
        if not os.path.exists(test_image):
            print(f"✗ 测试图片不存在: {test_image}\n")
            return False
        
        print(f"1. 测试图片: {test_image}")
        print(f"   文件大小: {os.path.getsize(test_image)} 字节\n")
        
        # 创建上传目录
        upload_dir = create_upload_dir()
        print(f"2. 上传目录: {upload_dir}")
        print(f"   绝对路径: {os.path.abspath(upload_dir)}\n")
        
        # 生成文件名
        filename = generate_unique_filename("test.jpg", 999)
        print(f"3. 生成文件名: {filename}\n")
        
        # 构造文件路径
        file_path = os.path.join(upload_dir, filename)
        file_path = os.path.abspath(file_path)
        print(f"4. 目标路径: {file_path}\n")
        
        # 模拟Streamlit的文件读取
        with open(test_image, "rb") as f:
            file_bytes = f.read()
        
        print(f"5. 读取文件内容: {len(file_bytes)} 字节\n")
        
        # 保存文件（模拟upload_file中的逻辑）
        print("6. 保存文件...")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # 验证文件
        print("7. 验证文件保存...\n")
        
        if not os.path.exists(file_path):
            print(f"   ✗ 文件不存在！")
            return False
        
        print(f"   ✓ 文件存在")
        
        saved_size = os.path.getsize(file_path)
        print(f"   ✓ 文件大小: {saved_size} 字节")
        
        if saved_size == 0:
            print(f"   ✗ 文件为空！")
            return False
        
        print(f"   ✓ 文件非空")
        
        if saved_size != len(file_bytes):
            print(f"   ⚠ 文件大小不匹配！")
            print(f"     期望: {len(file_bytes)} 字节")
            print(f"     实际: {saved_size} 字节")
        else:
            print(f"   ✓ 文件大小匹配\n")
        
        # 清理
        os.remove(file_path)
        print("8. 测试文件已清理\n")
        
        print("✓ 文件保存流程测试通过！\n")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_streamlit_file_upload():
    """模拟Streamlit文件上传行为"""
    print("="*60)
    print("4. 模拟Streamlit文件上传")
    print("="*60 + "\n")
    
    try:
        # 创建一个模拟的UploadedFile对象
        class MockUploadedFile:
            def __init__(self, filepath):
                self.name = os.path.basename(filepath)
                self._filepath = filepath
                self._content = None
            
            def read(self):
                if self._content is None:
                    with open(self._filepath, "rb") as f:
                        self._content = f.read()
                return self._content
        
        # 使用测试图片
        test_image = r"d:\hello_ai\1.jpg"
        
        if not os.path.exists(test_image):
            print(f"✗ 测试图片不存在\n")
            return False
        
        mock_file = MockUploadedFile(test_image)
        print(f"1. 模拟上传文件: {mock_file.name}")
        
        # 测试upload_file函数
        from database import get_user_by_account_id
        from certificate_processor import CertificateProcessor
        
        # 获取测试用户
        user = get_user_by_account_id("admin001")
        if not user:
            print("✗ 未找到测试用户\n")
            return False
        
        print(f"2. 使用测试用户: {user.name}\n")
        
        processor = CertificateProcessor(user)
        
        print("3. 调用upload_file...\n")
        success, file_path, message = processor.upload_file(mock_file)
        
        if success:
            print(f"   ✓ 上传成功: {message}")
            print(f"   ✓ 文件路径: {file_path}")
            print(f"   ✓ 文件存在: {os.path.exists(file_path)}")
            
            if os.path.exists(file_path):
                print(f"   ✓ 文件大小: {os.path.getsize(file_path)} 字节\n")
                # 清理
                os.remove(file_path)
                print("   测试文件已清理\n")
            
            print("✓ Streamlit文件上传模拟测试通过！\n")
            return True
        else:
            print(f"   ✗ 上传失败: {message}\n")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def check_common_issues():
    """检查常见问题"""
    print("="*60)
    print("5. 检查常见问题")
    print("="*60 + "\n")
    
    issues = []
    
    # 1. 检查uploads目录
    if not os.path.exists("uploads"):
        issues.append("uploads目录不存在")
    
    # 2. 检查工作目录
    cwd = os.getcwd()
    expected_dir = r"d:\hello_ai\zsSystem"
    if cwd.lower() != expected_dir.lower():
        issues.append(f"工作目录不正确：期望 {expected_dir}，实际 {cwd}")
    
    # 3. 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.getcwd())
        free_mb = free / (1024 * 1024)
        if free_mb < 100:
            issues.append(f"磁盘空间不足：仅剩 {free_mb:.1f} MB")
        else:
            print(f"✓ 磁盘空间充足: {free_mb:.1f} MB 可用\n")
    except:
        pass
    
    if issues:
        print("发现以下问题：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()
        return False
    else:
        print("✓ 未发现常见问题\n")
        return True


def main():
    """主诊断流程"""
    print("\n" + "="*60)
    print("文件上传问题诊断工具")
    print("="*60 + "\n")
    
    results = []
    
    # 运行所有测试
    results.append(("目录权限检查", check_directory_permissions()))
    results.append(("创建上传目录", test_create_upload_dir()))
    results.append(("文件保存流程", test_file_save_process()))
    results.append(("Streamlit上传模拟", test_streamlit_file_upload()))
    results.append(("常见问题检查", check_common_issues()))
    
    # 输出结果
    print("="*60)
    print("诊断结果汇总")
    print("="*60 + "\n")
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("="*60 + "\n")
    
    if passed == total:
        print("🎉 所有测试通过！文件上传功能正常。")
        print("\n建议：如果仍然遇到问题，请检查：")
        print("1. Streamlit应用是否在正确的目录下运行")
        print("2. 上传的文件是否符合格式和大小要求")
        print("3. 浏览器控制台是否有JavaScript错误")
    else:
        print("⚠ 发现问题！请根据上述测试结果排查。")
        print("\n常见解决方案：")
        print("1. 确保在 d:\\hello_ai\\zsSystem 目录下运行")
        print("2. 手动创建 uploads 目录")
        print("3. 检查文件系统权限")
        print("4. 确保有足够的磁盘空间")


if __name__ == "__main__":
    main()
