"""
Poppler安装和配置工具
用于解决PDF转换失败问题
"""
import os
import sys
import zipfile
import urllib.request
import platform


def check_poppler_installed():
    """检查poppler是否已安装"""
    print("检查poppler安装状态...")
    
    # 检查PATH中是否有pdftoppm
    import subprocess
    try:
        result = subprocess.run(['pdftoppm', '-v'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        print(f"✓ Poppler已安装")
        print(f"  版本信息: {result.stderr.strip()}")
        return True
    except FileNotFoundError:
        print("✗ Poppler未安装或未配置到PATH")
        return False
    except Exception as e:
        print(f"✗ 检查失败: {str(e)}")
        return False


def download_poppler_windows():
    """下载Windows版本的poppler"""
    print("\n开始下载Poppler for Windows...")
    
    # poppler下载链接（使用官方预编译版本）
    url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.08.0-0/Release-23.08.0-0.zip"
    download_path = "poppler-windows.zip"
    
    print(f"下载地址: {url}")
    print("这可能需要几分钟，请耐心等待...")
    
    try:
        urllib.request.urlretrieve(url, download_path)
        print(f"✓ 下载完成: {download_path}")
        return download_path
    except Exception as e:
        print(f"✗ 下载失败: {str(e)}")
        print("\n请手动下载poppler:")
        print("1. 访问: https://github.com/oschwartz10612/poppler-windows/releases")
        print("2. 下载最新的 Release-*.zip 文件")
        print("3. 解压到本目录")
        return None


def install_poppler(zip_path):
    """安装poppler到本地目录"""
    print("\n开始安装Poppler...")
    
    install_dir = os.path.join(os.getcwd(), "poppler")
    
    try:
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # 查找poppler目录
        extracted_dirs = [d for d in os.listdir(".") if d.startswith("poppler")]
        if not extracted_dirs:
            print("✗ 未找到解压的poppler目录")
            return None
        
        poppler_dir = extracted_dirs[0]
        
        # 重命名为poppler
        if os.path.exists(install_dir):
            import shutil
            shutil.rmtree(install_dir)
        
        os.rename(poppler_dir, install_dir)
        
        print(f"✓ Poppler已安装到: {install_dir}")
        
        # 查找bin目录
        bin_dir = os.path.join(install_dir, "Library", "bin")
        if not os.path.exists(bin_dir):
            bin_dir = os.path.join(install_dir, "bin")
        
        if os.path.exists(bin_dir):
            print(f"✓ bin目录位置: {bin_dir}")
            return bin_dir
        else:
            print("✗ 未找到bin目录")
            return None
            
    except Exception as e:
        print(f"✗ 安装失败: {str(e)}")
        return None


def add_to_path(bin_dir):
    """添加到PATH环境变量"""
    print("\n配置环境变量...")
    
    # 获取当前PATH
    current_path = os.environ.get('PATH', '')
    
    if bin_dir in current_path:
        print("✓ PATH中已包含poppler")
        return True
    
    # 添加到当前进程的PATH
    os.environ['PATH'] = bin_dir + os.pathsep + current_path
    
    print(f"✓ 已添加到当前会话PATH: {bin_dir}")
    print("\n注意：这只对当前Python进程有效。")
    print("\n要永久添加到PATH，请：")
    print("1. 按Win+R，输入 sysdm.cpl")
    print("2. 点击【高级】->【环境变量】")
    print("3. 在【系统变量】或【用户变量】中找到Path")
    print("4. 点击【编辑】->【新建】")
    print(f"5. 添加路径: {bin_dir}")
    print("6. 点击【确定】保存")
    
    return True


def test_pdf_conversion():
    """测试PDF转换功能"""
    print("\n测试PDF转换功能...")
    
    try:
        from pdf2image import convert_from_path
        
        # 创建一个测试PDF
        test_pdf = "test_poppler.pdf"
        
        # 使用reportlab创建简单PDF
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(test_pdf)
            c.drawString(100, 750, "Test PDF for Poppler")
            c.save()
            print(f"✓ 创建测试PDF: {test_pdf}")
        except ImportError:
            print("⚠ 跳过PDF创建（需要reportlab）")
            return False
        
        # 转换PDF
        images = convert_from_path(test_pdf, first_page=1, last_page=1)
        
        if images:
            print(f"✓ PDF转换成功！")
            print(f"  转换了 {len(images)} 页")
            print(f"  图片尺寸: {images[0].size}")
            
            # 清理测试文件
            os.remove(test_pdf)
            
            return True
        else:
            print("✗ PDF转换失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def create_poppler_config():
    """创建poppler配置文件"""
    config_content = f"""# Poppler配置
# 此文件由install_poppler.py自动生成

import os
import sys

# Poppler路径
POPPLER_PATH = r"{os.path.join(os.getcwd(), 'poppler', 'Library', 'bin')}"

# 添加到PATH
if POPPLER_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')
    print(f"已添加Poppler到PATH: {{POPPLER_PATH}}")
"""
    
    config_file = "poppler_config.py"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"\n✓ 已创建配置文件: {config_file}")
    print("  在使用pdf2image前导入此文件即可自动配置poppler")


def main():
    """主安装流程"""
    print("="*60)
    print("Poppler安装和配置工具")
    print("="*60)
    
    # 检查操作系统
    if platform.system() != 'Windows':
        print("\n此工具仅支持Windows系统")
        print("Linux/Mac用户请使用包管理器安装：")
        print("  Linux: sudo apt-get install poppler-utils")
        print("  Mac: brew install poppler")
        return
    
    # 步骤1：检查是否已安装
    if check_poppler_installed():
        print("\nPoppler已正确安装和配置！")
        
        # 测试转换功能
        test_pdf_conversion()
        return
    
    # 步骤2：询问用户选择
    print("\nPoppler未安装。请选择安装方式：")
    print("1. 自动下载并安装（推荐）")
    print("2. 手动安装指引")
    print("3. 退出")
    
    choice = input("\n请输入选择(1-3): ").strip()
    
    if choice == '1':
        # 自动安装
        zip_path = download_poppler_windows()
        if not zip_path:
            return
        
        bin_dir = install_poppler(zip_path)
        if not bin_dir:
            return
        
        add_to_path(bin_dir)
        create_poppler_config()
        
        # 清理下载文件
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"\n清理下载文件: {zip_path}")
        
        # 测试
        print("\n" + "="*60)
        if test_pdf_conversion():
            print("\n🎉 Poppler安装成功！")
        else:
            print("\n⚠ Poppler已安装，但测试失败")
            print("   请重启Python并重新测试")
        
    elif choice == '2':
        # 手动安装指引
        print("\n手动安装步骤：")
        print("1. 下载Poppler for Windows：")
        print("   https://github.com/oschwartz10612/poppler-windows/releases")
        print("\n2. 解压到任意目录，例如：")
        print("   C:\\Program Files\\poppler")
        print("\n3. 将bin目录添加到系统PATH：")
        print("   例如：C:\\Program Files\\poppler\\Library\\bin")
        print("\n4. 重启Python/CMD窗口")
        print("\n5. 运行此脚本验证安装")
    else:
        print("\n已退出")


if __name__ == "__main__":
    main()
