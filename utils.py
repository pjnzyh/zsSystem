"""
工具函数模块
提供文件处理、数据验证等辅助功能
"""
import os
import base64
import re
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image
import io


def validate_account_id(account_id: str, role: str) -> Tuple[bool, str]:
    """
    验证学（工）号格式
    学生：13位数字
    教师：8位数字
    """
    if not account_id.isdigit():
        return False, "学（工）号必须为数字"
    
    if role == "student":
        if len(account_id) != 13:
            return False, "学生学号必须为13位数字"
    elif role == "teacher":
        if len(account_id) != 8:
            return False, "教师工号必须为8位数字"
    else:
        return False, "无效的角色类型"
    
    return True, ""


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码强度
    至少8位，包含字母和数字
    """
    if len(password) < 8:
        return False, "密码至少需要8位"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_letter and has_digit):
        return False, "密码必须包含字母和数字"
    
    return True, ""


def validate_file_type(filename: str) -> Tuple[bool, str]:
    """验证文件类型"""
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp'}
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in allowed_extensions:
        return False, f"不支持的文件格式，仅支持：{', '.join(allowed_extensions)}"
    
    return True, ext


def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
    """验证文件大小（默认最大10MB）"""
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"文件大小超过限制（最大 {max_mb:.1f}MB）"
    
    return True, ""


def image_to_base64(image_path: str) -> str:
    """将图片转换为Base64编码"""
    with open(image_path, "rb") as img_file:
        img_base = base64.b64encode(img_file.read()).decode("utf-8")
    return img_base


def bytes_to_base64(image_bytes: bytes) -> str:
    """将图片字节转换为Base64编码"""
    return base64.b64encode(image_bytes).decode("utf-8")


def pdf_to_image(pdf_path: str, output_path: Optional[str] = None) -> str:
    """
    将PDF转换为图片（只转换第一页）
    返回图片路径
    """
    try:
        from pdf2image import convert_from_path
        from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
        
        # 检查PDF文件是否存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 检查文件大小
        if os.path.getsize(pdf_path) == 0:
            raise ValueError("PDF文件为空")
        
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1)
        except PDFInfoNotInstalledError:
            raise Exception(
                "Poppler未安装或未配置到PATH。\n"
                "请运行以下命令安装：\n"
                "  python install_poppler.py\n"
                "或手动安装poppler并添加到系统PATH环境变量。\n"
                "详细说明请查看README.md中的'PDF支持'部分。"
            )
        except PDFPageCountError:
            raise Exception(
                "无法读取PDF页数。可能的原因：\n"
                "1. PDF文件损坏\n"
                "2. PDF文件受密码保护\n"
                "3. Poppler版本不兼容\n"
                "建议：将PDF转换为图片格式后重新上传。"
            )
        
        if not images:
            raise ValueError("PDF转换失败：无法提取页面")
        
        # 如果没有指定输出路径，使用临时路径
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '_page1.png')
        
        # 保存转换后的图片
        images[0].save(output_path, 'PNG')
        
        # 验证输出文件
        if not os.path.exists(output_path):
            raise Exception("图片保存失败")
        
        if os.path.getsize(output_path) == 0:
            raise Exception("生成的图片文件为空")
        
        return output_path
        
    except ImportError as e:
        raise Exception(
            f"pdf2image库未安装或导入失败: {str(e)}\n"
            "请运行: pip install pdf2image"
        )
    except Exception as e:
        # 如果错误信息中包含poppler相关关键词，提供安装指引
        error_msg = str(e).lower()
        if 'poppler' in error_msg or 'pdftoppm' in error_msg or 'path' in error_msg:
            raise Exception(
                f"PDF转换失败: {str(e)}\n\n"
                "这通常是因为Poppler未安装。解决方法：\n"
                "1. 运行安装脚本: python install_poppler.py\n"
                "2. 或手动下载Poppler: https://github.com/oschwartz10612/poppler-windows/releases\n"
                "3. 解压后将bin目录添加到系统PATH环境变量\n\n"
                "临时解决方案：将PDF转换为JPG/PNG格式后上传。"
            )
        else:
            raise Exception(f"PDF转换失败: {str(e)}")


def resize_image_if_needed(image_path: str, max_size: int = 2048) -> str:
    """
    如果图片尺寸过大则调整大小
    返回处理后的图片路径
    """
    try:
        # 确保使用绝对路径
        abs_path = os.path.abspath(image_path)
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"图片文件不存在: {abs_path}")
        
        # 检查文件大小，避免空文件
        if os.path.getsize(abs_path) == 0:
            raise ValueError(f"图片文件为空: {abs_path}")
        
        # 打开图片
        img = Image.open(abs_path)
        width, height = img.size
        
        if width > max_size or height > max_size:
            # 计算新尺寸（保持比例）
            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # 调整大小
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存到临时文件
            resized_path = abs_path.replace(os.path.splitext(abs_path)[1], '_resized.png')
            img.save(resized_path, 'PNG')
            img.close()
            return resized_path
        
        img.close()
        return abs_path
    except Exception as e:
        raise Exception(f"图片处理失败: {str(e)}")


def format_date(date_str: str) -> Optional[str]:
    """
    格式化日期字符串
    尝试多种日期格式并统一返回 YYYY-MM-DD 格式
    """
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y年%m月%d日",
        "%Y.%m.%d",
        "%Y%m%d"
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None


def extract_student_id(text: str) -> Optional[str]:
    """
    从文本中提取13位学号
    """
    pattern = r'\b\d{13}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def create_upload_dir(base_dir: str = "uploads") -> str:
    """创建上传目录"""
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # 按日期创建子目录
    date_dir = datetime.now().strftime("%Y%m%d")
    full_path = os.path.join(base_dir, date_dir)
    
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    
    return full_path


def generate_unique_filename(original_filename: str, user_id: int) -> str:
    """生成唯一文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(original_filename)[1]
    return f"user{user_id}_{timestamp}{ext}"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
