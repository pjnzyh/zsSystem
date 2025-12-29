"""
快速配置poppler路径
适用于已下载poppler但未添加到PATH的情况
"""
import os
import sys


def find_poppler_bin():
    """查找可能的poppler安装位置"""
    print("正在搜索poppler安装位置...")
    
    possible_paths = [
        # 当前目录
        os.path.join(os.getcwd(), "poppler", "Library", "bin"),
        os.path.join(os.getcwd(), "poppler", "bin"),
        
        # Program Files
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\bin",
        
        # D盘
        r"D:\poppler\Library\bin",
        r"D:\poppler\bin",
        
        # 用户目录
        os.path.join(os.path.expanduser("~"), "poppler", "Library", "bin"),
        os.path.join(os.path.expanduser("~"), "poppler", "bin"),
    ]
    
    found_paths = []
    
    for path in possible_paths:
        if os.path.exists(path):
            # 检查是否包含pdftoppm.exe
            pdftoppm = os.path.join(path, "pdftoppm.exe")
            if os.path.exists(pdftoppm):
                found_paths.append(path)
                print(f"  ✓ 找到: {path}")
    
    return found_paths


def add_to_current_env(bin_path):
    """添加到当前Python进程的环境变量"""
    current_path = os.environ.get('PATH', '')
    
    if bin_path in current_path:
        print(f"\n✓ PATH中已包含: {bin_path}")
        return True
    
    os.environ['PATH'] = bin_path + os.pathsep + current_path
    print(f"\n✓ 已添加到当前进程PATH: {bin_path}")
    return True


def test_poppler():
    """测试poppler是否可用"""
    print("\n测试poppler...")
    
    import subprocess
    try:
        result = subprocess.run(['pdftoppm', '-v'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        print("✓ Poppler可用")
        print(f"  {result.stderr.strip()}")
        return True
    except FileNotFoundError:
        print("✗ Poppler仍然不可用")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def create_startup_script(bin_path):
    """创建启动脚本，自动配置PATH"""
    
    # 创建Windows批处理脚本
    bat_content = f"""@echo off
REM 自动配置poppler PATH并启动应用

REM 添加poppler到PATH
set PATH={bin_path};%PATH%

REM 启动Streamlit应用
streamlit run app.py

pause
"""
    
    bat_file = "start_with_poppler.bat"
    with open(bat_file, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"\n✓ 已创建启动脚本: {bat_file}")
    print("  以后可以双击此脚本启动应用")
    
    # 创建Python配置模块
    py_content = f"""# poppler路径配置
# 此文件由setup_poppler_path.py自动生成

import os

POPPLER_BIN_PATH = r"{bin_path}"

# 自动添加到PATH
if POPPLER_BIN_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] = POPPLER_BIN_PATH + os.pathsep + os.environ.get('PATH', '')
    print(f"已配置poppler: {{POPPLER_BIN_PATH}}")
"""
    
    py_file = "poppler_config.py"
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write(py_content)
    
    print(f"✓ 已创建配置模块: {py_file}")
    print("  在app.py开头添加: import poppler_config")


def show_permanent_setup_guide(bin_path):
    """显示永久配置指南"""
    print("\n" + "="*60)
    print("永久配置指南（推荐）")
    print("="*60)
    print("\n将poppler永久添加到系统PATH：")
    print("\n1. 按 Win+R，输入: sysdm.cpl")
    print("2. 点击【高级】->【环境变量】")
    print("3. 在【系统变量】中找到 Path，点击【编辑】")
    print("4. 点击【新建】")
    print(f"5. 输入: {bin_path}")
    print("6. 点击【确定】保存")
    print("7. 重启命令行窗口")
    print("\n这样以后就不需要每次手动配置了。")


def main():
    print("="*60)
    print("Poppler路径快速配置工具")
    print("="*60)
    
    # 步骤1：查找poppler
    found_paths = find_poppler_bin()
    
    if not found_paths:
        print("\n✗ 未找到poppler安装")
        print("\n请先安装poppler：")
        print("  方法1: python install_poppler.py")
        print("  方法2: 参考 PDF支持配置指南.md")
        return
    
    # 步骤2：选择路径
    if len(found_paths) == 1:
        selected_path = found_paths[0]
        print(f"\n使用找到的poppler: {selected_path}")
    else:
        print(f"\n找到 {len(found_paths)} 个poppler安装位置：")
        for i, path in enumerate(found_paths, 1):
            print(f"{i}. {path}")
        
        choice = input(f"\n请选择使用哪一个(1-{len(found_paths)}): ").strip()
        try:
            idx = int(choice) - 1
            selected_path = found_paths[idx]
        except (ValueError, IndexError):
            print("无效选择，使用第一个")
            selected_path = found_paths[0]
    
    # 步骤3：配置环境变量
    add_to_current_env(selected_path)
    
    # 步骤4：测试
    if test_poppler():
        print("\n🎉 配置成功！")
        
        # 步骤5：创建启动脚本
        create_startup_script(selected_path)
        
        # 步骤6：显示永久配置指南
        show_permanent_setup_guide(selected_path)
        
        print("\n" + "="*60)
        print("下一步")
        print("="*60)
        print("\n临时使用（当前会话）：")
        print("  直接运行: streamlit run app.py")
        print("\n或使用启动脚本：")
        print("  双击: start_with_poppler.bat")
        print("\n或在app.py开头添加：")
        print("  import poppler_config")
        
    else:
        print("\n✗ 配置失败")
        print("请尝试手动配置，参考 PDF支持配置指南.md")


if __name__ == "__main__":
    main()
