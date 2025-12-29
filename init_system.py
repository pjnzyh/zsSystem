"""
系统初始化脚本
一键完成环境检查、数据库初始化等准备工作
"""
import os
import sys


def check_dependencies():
    """检查依赖包是否已安装"""
    print("正在检查依赖包...")
    
    required_packages = [
        'streamlit',
        'sqlmodel',
        'pandas',
        'openpyxl',
        'PIL',
        'pdf2image',
        'zhipuai',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n缺少以下依赖包，请先安装：")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n或者运行：")
        print("pip install -r requirements.txt")
        return False
    
    print("\n所有依赖包已安装！")
    return True


def initialize_database():
    """初始化数据库"""
    print("\n正在初始化数据库...")
    
    try:
        from database import init_database
        init_database()
        print("✓ 数据库初始化完成！")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        return False


def create_directories():
    """创建必要的目录"""
    print("\n正在创建必要的目录...")
    
    directories = ['uploads']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ 创建目录: {directory}")
        else:
            print(f"✓ 目录已存在: {directory}")
    
    return True


def check_poppler():
    """检查poppler是否安装（用于PDF转换）"""
    print("\n正在检查poppler（PDF转换工具）...")
    
    try:
        from pdf2image import convert_from_path
        # 尝试导入，如果poppler未安装会报错
        print("✓ poppler已安装")
        return True
    except Exception as e:
        print("⚠ poppler未安装或未配置")
        print("  如需处理PDF文件，请安装poppler：")
        print("  - Windows: 下载poppler并添加到PATH")
        print("  - Linux: sudo apt-get install poppler-utils")
        print("  - macOS: brew install poppler")
        return False


def show_system_info():
    """显示系统信息"""
    print("\n" + "="*60)
    print("竞赛证书智能识别与信息管理系统")
    print("="*60)
    print("\n默认管理员账号：")
    print("  账号: admin001")
    print("  密码: admin123")
    print("\n启动命令：")
    print("  streamlit run app.py")
    print("\n访问地址：")
    print("  http://localhost:8501")
    print("\n" + "="*60)


def main():
    """主函数"""
    print("开始系统初始化...\n")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        sys.exit(1)
    
    # 初始化数据库
    if not initialize_database():
        sys.exit(1)
    
    # 检查poppler（可选）
    check_poppler()
    
    # 显示系统信息
    show_system_info()
    
    print("\n初始化完成！您现在可以启动系统了。\n")


if __name__ == "__main__":
    main()
