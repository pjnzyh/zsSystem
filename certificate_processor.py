"""
证书处理模块
实现文件上传、信息提取、数据保存
"""
import os
import sys
from typing import Optional, Tuple, Dict
from datetime import datetime

# 修复Streamlit Cloud路径问题
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from models import Certificate, FileRecord, User
from database import get_session
from utils import (
    validate_file_type, validate_file_size, create_upload_dir,
    generate_unique_filename, pdf_to_image, resize_image_if_needed,
    format_date
)
from api_client import CertificateExtractor


class CertificateProcessor:
    """证书处理器"""
    
    def __init__(self, user: User):
        """
        初始化处理器
        
        Args:
            user: 当前用户对象
        """
        self.user = user
        self.extractor = CertificateExtractor()
    
    def upload_file(self, uploaded_file) -> Tuple[bool, Optional[str], str]:
        """
        上传证书文件
        
        Args:
            uploaded_file: Streamlit上传的文件对象
            
        Returns:
            (成功标志, 文件路径, 消息)
        """
        try:
            # 验证文件类型
            valid, ext_or_msg = validate_file_type(uploaded_file.name)
            if not valid:
                return False, None, ext_or_msg
            
            file_ext = ext_or_msg
            
            # 读取文件内容
            try:
                # 确保文件指针在开始位置
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
            except Exception as e:
                return False, None, f"文件读取失败: {str(e)}"
            
            # 验证文件大小
            file_size = len(file_bytes)
            
            if file_size == 0:
                return False, None, "文件为空，请选择有效的文件"
            
            valid, msg = validate_file_size(file_size)
            if not valid:
                return False, None, msg
            
            # 创建上传目录
            try:
                upload_dir = create_upload_dir()
            except Exception as e:
                return False, None, f"创建上传目录失败: {str(e)}"
            
            # 生成唯一文件名
            filename = generate_unique_filename(uploaded_file.name, self.user.user_id)
            file_path = os.path.join(upload_dir, filename)
            
            # 转换为绝对路径
            file_path = os.path.abspath(file_path)
            
            # 保存文件
            try:
                with open(file_path, "wb") as f:
                    f.write(file_bytes)
            except PermissionError:
                return False, None, f"无权限写入文件: {file_path}"
            except IOError as e:
                return False, None, f"文件写入失败: {str(e)}"
            except Exception as e:
                return False, None, f"保存文件时发生错误: {str(e)}"
            
            # 验证文件是否成功写入
            if not os.path.exists(file_path):
                return False, None, f"文件保存失败：文件不存在 ({file_path})"
            
            saved_size = os.path.getsize(file_path)
            if saved_size == 0:
                return False, None, f"文件保存失败：文件为空 ({file_path})"
            
            if saved_size != file_size:
                return False, None, f"文件保存不完整：期望 {file_size} 字节，实际 {saved_size} 字节"
            
            # 记录到数据库
            try:
                file_type = "pdf" if file_ext == ".pdf" else "image"
                with get_session() as session:
                    file_record = FileRecord(
                        user_id=self.user.user_id,
                        file_name=uploaded_file.name,
                        file_path=file_path,
                        file_type=file_type,
                        file_size=file_size
                    )
                    session.add(file_record)
                    session.commit()
            except Exception as e:
                # 数据库记录失败不影响文件上传，仅记录警告
                import logging
                logging.warning(f"文件记录到数据库失败: {str(e)}")
            
            return True, file_path, "文件上传成功"
            
        except Exception as e:
            return False, None, f"文件上传失败: {str(e)}"
    
    def extract_certificate_info(self, file_path: str) -> Tuple[bool, Dict, str]:
        """
        从证书文件中提取信息
        
        Args:
            file_path: 证书文件路径
            
        Returns:
            (成功标志, 提取的数据, 消息)
        """
        try:
            # 转换为绝对路径
            abs_file_path = os.path.abspath(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(abs_file_path):
                return False, {}, f"文件不存在: {abs_file_path}"
            
            # 判断文件类型
            ext = os.path.splitext(abs_file_path)[1].lower()
            
            # 如果是PDF，先转换为图片
            if ext == '.pdf':
                try:
                    image_path = pdf_to_image(abs_file_path)
                except Exception as e:
                    return False, {}, f"PDF转换失败: {str(e)}"
            else:
                image_path = abs_file_path
            
            # 如果图片太大，调整大小
            try:
                image_path = resize_image_if_needed(image_path)
            except Exception as e:
                return False, {}, f"图片处理失败: {str(e)}"
            
            # 调用API提取信息
            success, data, error_msg = self.extractor.extract_from_image(image_path)
            
            if not success:
                return False, {}, error_msg
            
            # 根据用户角色自动填充某些字段
            if self.user.role == "student":
                # 学生用户：自动填充学号和姓名
                data["student_id"] = self.user.account_id
                data["student_name"] = self.user.name
            elif self.user.role == "teacher":
                # 教师用户：自动填充指导教师
                data["advisor"] = self.user.name
            
            # 格式化日期
            if data.get("award_date"):
                formatted_date = format_date(data["award_date"])
                if formatted_date:
                    data["award_date"] = formatted_date
            
            return True, data, "信息提取成功"
            
        except Exception as e:
            return False, {}, f"信息提取失败: {str(e)}"
    
    def save_draft(self, file_path: str, cert_data: Dict) -> Tuple[bool, Optional[int], str]:
        """
        保存证书草稿
        
        Args:
            file_path: 证书文件路径
            cert_data: 证书数据
            
        Returns:
            (成功标志, 证书ID, 消息)
        """
        try:
            with get_session() as session:
                certificate = Certificate(
                    submitter_id=self.user.user_id,
                    submitter_role=self.user.role,
                    student_id=cert_data.get("student_id", ""),
                    student_name=cert_data.get("student_name", ""),
                    department=cert_data.get("department"),
                    competition_name=cert_data.get("competition_name"),
                    award_category=cert_data.get("award_category"),
                    award_level=cert_data.get("award_level"),
                    competition_type=cert_data.get("competition_type"),
                    organizer=cert_data.get("organizer"),
                    award_date=cert_data.get("award_date"),
                    advisor=cert_data.get("advisor", ""),
                    file_path=file_path,
                    extraction_method="glm4v",
                    status="draft"
                )
                session.add(certificate)
                session.commit()
                session.refresh(certificate)
                
                return True, certificate.cert_id, "草稿保存成功"
        except Exception as e:
            return False, None, f"保存失败: {str(e)}"
    
    def submit_certificate(self, cert_data: Dict, file_path: str) -> Tuple[bool, str]:
        """
        提交证书信息
        
        Args:
            cert_data: 证书数据
            file_path: 证书文件路径
            
        Returns:
            (成功标志, 消息)
        """
        # 验证必填字段
        required_fields = ["student_id", "student_name", "advisor"]
        for field in required_fields:
            if not cert_data.get(field):
                field_names = {
                    "student_id": "学号",
                    "student_name": "学生姓名",
                    "advisor": "指导教师"
                }
                return False, f"请填写{field_names[field]}"
        
        # 验证学号格式
        if len(cert_data["student_id"]) != 13:
            return False, "学号必须为13位"
        
        try:
            with get_session() as session:
                certificate = Certificate(
                    submitter_id=self.user.user_id,
                    submitter_role=self.user.role,
                    student_id=cert_data["student_id"],
                    student_name=cert_data["student_name"],
                    department=cert_data.get("department"),
                    competition_name=cert_data.get("competition_name"),
                    award_category=cert_data.get("award_category"),
                    award_level=cert_data.get("award_level"),
                    competition_type=cert_data.get("competition_type"),
                    organizer=cert_data.get("organizer"),
                    award_date=cert_data.get("award_date"),
                    advisor=cert_data["advisor"],
                    file_path=file_path,
                    extraction_method="glm4v",
                    status="submitted",
                    submitted_at=datetime.now()
                )
                session.add(certificate)
                session.commit()
                
                return True, "证书提交成功！"
        except Exception as e:
            return False, f"提交失败: {str(e)}"
    
    def get_my_certificates(self, status_filter: Optional[str] = None):
        """
        获取当前用户的证书列表
        
        Args:
            status_filter: 状态筛选（draft/submitted），None表示全部
            
        Returns:
            证书列表
        """
        with get_session() as session:
            query = select(Certificate).where(
                Certificate.submitter_id == self.user.user_id
            )
            
            if status_filter:
                query = query.where(Certificate.status == status_filter)
            
            certificates = session.exec(query).all()
            return list(certificates)
    
    def update_certificate(self, cert_id: int, cert_data: Dict) -> Tuple[bool, str]:
        """
        更新证书信息（仅草稿状态可更新）
        
        Args:
            cert_id: 证书ID
            cert_data: 新的证书数据
            
        Returns:
            (成功标志, 消息)
        """
        try:
            with get_session() as session:
                certificate = session.exec(
                    select(Certificate).where(
                        Certificate.cert_id == cert_id,
                        Certificate.submitter_id == self.user.user_id
                    )
                ).first()
                
                if not certificate:
                    return False, "证书不存在或无权限"
                
                if certificate.status == "submitted":
                    return False, "已提交的证书不可修改"
                
                # 更新字段
                certificate.student_id = cert_data.get("student_id", certificate.student_id)
                certificate.student_name = cert_data.get("student_name", certificate.student_name)
                certificate.department = cert_data.get("department")
                certificate.competition_name = cert_data.get("competition_name")
                certificate.award_category = cert_data.get("award_category")
                certificate.award_level = cert_data.get("award_level")
                certificate.competition_type = cert_data.get("competition_type")
                certificate.organizer = cert_data.get("organizer")
                certificate.award_date = cert_data.get("award_date")
                certificate.advisor = cert_data.get("advisor", certificate.advisor)
                
                session.add(certificate)
                session.commit()
                
                return True, "更新成功"
        except Exception as e:
            return False, f"更新失败: {str(e)}"
    
    def delete_certificate(self, cert_id: int) -> Tuple[bool, str]:
        """
        删除证书（仅草稿状态可删除）
        
        Args:
            cert_id: 证书ID
            
        Returns:
            (成功标志, 消息)
        """
        try:
            with get_session() as session:
                certificate = session.exec(
                    select(Certificate).where(
                        Certificate.cert_id == cert_id,
                        Certificate.submitter_id == self.user.user_id
                    )
                ).first()
                
                if not certificate:
                    return False, "证书不存在或无权限"
                
                if certificate.status == "submitted":
                    return False, "已提交的证书不可删除"
                
                session.delete(certificate)
                session.commit()
                
                return True, "删除成功"
        except Exception as e:
            return False, f"删除失败: {str(e)}"
