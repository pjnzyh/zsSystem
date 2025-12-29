"""
管理员功能模块
实现用户管理、数据导出、批量导入
"""
import os
import sys
import pandas as pd
from typing import Tuple, List, Dict
from datetime import datetime

# 修复Streamlit Cloud路径问题
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from models import User, Certificate, FileRecord
from database import get_session
from auth import hash_password, validate_account_id, validate_email


class AdminManager:
    """管理员管理器"""
    
    def __init__(self, admin_user: User):
        """
        初始化管理器
        
        Args:
            admin_user: 管理员用户对象
        """
        if admin_user.role != "admin":
            raise ValueError("只有管理员可以使用此功能")
        
        self.admin_user = admin_user
    
    def import_users_from_excel(self, excel_file) -> Tuple[bool, Dict, str]:
        """
        从Excel文件批量导入用户
        
        Args:
            excel_file: Excel文件对象
            
        Returns:
            (成功标志, 统计信息, 消息)
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file)
            
            # 验证必填列
            required_columns = ['学（工）号', '姓名', '角色类型', '单位', '邮箱']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, {}, f"缺少必填列: {', '.join(missing_columns)}"
            
            # 统计信息
            stats = {
                "total": len(df),
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "errors": []
            }
            
            with get_session() as session:
                for index, row in df.iterrows():
                    try:
                        account_id = str(row['学（工）号']).strip()
                        name = str(row['姓名']).strip()
                        role = str(row['角色类型']).strip().lower()
                        department = str(row['单位']).strip()
                        email = str(row['邮箱']).strip()
                        
                        # 获取密码（如果没有提供则自动生成）
                        if '初始密码' in df.columns and pd.notna(row['初始密码']):
                            password = str(row['初始密码']).strip()
                        else:
                            password = f"{account_id}@123"  # 默认密码
                        
                        # 角色类型转换
                        if role in ['学生', 'student']:
                            role = 'student'
                        elif role in ['教师', 'teacher']:
                            role = 'teacher'
                        else:
                            stats["failed"] += 1
                            stats["errors"].append(f"第{index+2}行：无效的角色类型 '{role}'")
                            continue
                        
                        # 验证学（工）号格式
                        valid, msg = validate_account_id(account_id, role)
                        if not valid:
                            stats["failed"] += 1
                            stats["errors"].append(f"第{index+2}行：{msg}")
                            continue
                        
                        # 验证邮箱格式
                        if not validate_email(email):
                            stats["failed"] += 1
                            stats["errors"].append(f"第{index+2}行：邮箱格式不正确")
                            continue
                        
                        # 检查是否已存在
                        existing_user = session.exec(
                            select(User).where(User.account_id == account_id)
                        ).first()
                        
                        if existing_user:
                            stats["skipped"] += 1
                            stats["errors"].append(f"第{index+2}行：学（工）号 {account_id} 已存在")
                            continue
                        
                        # 创建用户
                        user = User(
                            account_id=account_id,
                            name=name,
                            role=role,
                            department=department,
                            email=email,
                            password_hash=hash_password(password),
                            created_by="admin_import"
                        )
                        session.add(user)
                        stats["success"] += 1
                        
                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append(f"第{index+2}行：{str(e)}")
                
                session.commit()
            
            message = f"导入完成！成功: {stats['success']}, 失败: {stats['failed']}, 跳过: {stats['skipped']}"
            return True, stats, message
            
        except Exception as e:
            return False, {}, f"导入失败: {str(e)}"
    
    def export_certificates_to_excel(self, output_path: str = None) -> Tuple[bool, str, str]:
        """
        导出所有证书数据到Excel
        
        Args:
            output_path: 输出文件路径，None则自动生成
            
        Returns:
            (成功标志, 文件路径, 消息)
        """
        try:
            with get_session() as session:
                # 查询所有已提交的证书
                certificates = session.exec(
                    select(Certificate).where(Certificate.status == "submitted")
                ).all()
                
                if not certificates:
                    return False, "", "暂无已提交的证书数据"
                
                # 构造数据
                data = []
                for cert in certificates:
                    # 获取提交者信息
                    submitter = session.exec(
                        select(User).where(User.user_id == cert.submitter_id)
                    ).first()
                    
                    data.append({
                        "证书ID": cert.cert_id,
                        "提交者学（工）号": submitter.account_id if submitter else "",
                        "提交者姓名": submitter.name if submitter else "",
                        "提交者角色": "学生" if cert.submitter_role == "student" else "教师",
                        "学生学号": cert.student_id,
                        "学生姓名": cert.student_name,
                        "学生所在学院": cert.department or "",
                        "竞赛项目": cert.competition_name or "",
                        "获奖类别": cert.award_category or "",
                        "获奖等级": cert.award_level or "",
                        "竞赛类型": cert.competition_type or "",
                        "主办单位": cert.organizer or "",
                        "获奖时间": cert.award_date or "",
                        "指导教师": cert.advisor,
                        "提交时间": cert.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if cert.submitted_at else ""
                    })
                
                # 创建DataFrame
                df = pd.DataFrame(data)
                
                # 生成输出路径
                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"证书数据导出_{timestamp}.xlsx"
                
                # 导出到Excel
                df.to_excel(output_path, index=False, engine='openpyxl')
                
                return True, output_path, f"成功导出 {len(certificates)} 条记录"
                
        except Exception as e:
            return False, "", f"导出失败: {str(e)}"
    
    def export_certificates_to_csv(self, output_path: str = None) -> Tuple[bool, str, str]:
        """
        导出所有证书数据到CSV
        
        Args:
            output_path: 输出文件路径，None则自动生成
            
        Returns:
            (成功标志, 文件路径, 消息)
        """
        try:
            with get_session() as session:
                # 查询所有已提交的证书
                certificates = session.exec(
                    select(Certificate).where(Certificate.status == "submitted")
                ).all()
                
                if not certificates:
                    return False, "", "暂无已提交的证书数据"
                
                # 构造数据
                data = []
                for cert in certificates:
                    # 获取提交者信息
                    submitter = session.exec(
                        select(User).where(User.user_id == cert.submitter_id)
                    ).first()
                    
                    data.append({
                        "证书ID": cert.cert_id,
                        "提交者学（工）号": submitter.account_id if submitter else "",
                        "提交者姓名": submitter.name if submitter else "",
                        "提交者角色": "学生" if cert.submitter_role == "student" else "教师",
                        "学生学号": cert.student_id,
                        "学生姓名": cert.student_name,
                        "学生所在学院": cert.department or "",
                        "竞赛项目": cert.competition_name or "",
                        "获奖类别": cert.award_category or "",
                        "获奖等级": cert.award_level or "",
                        "竞赛类型": cert.competition_type or "",
                        "主办单位": cert.organizer or "",
                        "获奖时间": cert.award_date or "",
                        "指导教师": cert.advisor,
                        "提交时间": cert.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if cert.submitted_at else ""
                    })
                
                # 创建DataFrame
                df = pd.DataFrame(data)
                
                # 生成输出路径
                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"证书数据导出_{timestamp}.csv"
                
                # 导出到CSV
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                
                return True, output_path, f"成功导出 {len(certificates)} 条记录"
                
        except Exception as e:
            return False, "", f"导出失败: {str(e)}"
    
    def get_statistics(self) -> Dict:
        """
        获取系统统计信息
        
        Returns:
            统计信息字典
        """
        with get_session() as session:
            # 用户统计
            total_users = session.exec(select(User)).all()
            student_count = len([u for u in total_users if u.role == "student"])
            teacher_count = len([u for u in total_users if u.role == "teacher"])
            admin_count = len([u for u in total_users if u.role == "admin"])
            
            # 证书统计
            all_certs = session.exec(select(Certificate)).all()
            submitted_certs = [c for c in all_certs if c.status == "submitted"]
            draft_certs = [c for c in all_certs if c.status == "draft"]
            
            # 按学院统计
            dept_stats = {}
            for cert in submitted_certs:
                if cert.department:
                    dept_stats[cert.department] = dept_stats.get(cert.department, 0) + 1
            
            # 按获奖等级统计
            award_stats = {}
            for cert in submitted_certs:
                if cert.award_level:
                    award_stats[cert.award_level] = award_stats.get(cert.award_level, 0) + 1
            
            return {
                "user_total": len(total_users),
                "student_count": student_count,
                "teacher_count": teacher_count,
                "admin_count": admin_count,
                "cert_total": len(all_certs),
                "cert_submitted": len(submitted_certs),
                "cert_draft": len(draft_certs),
                "dept_stats": dept_stats,
                "award_stats": award_stats
            }
    
    def get_all_certificates(self, filters: Dict = None):
        """
        获取所有证书（支持筛选）
        
        Args:
            filters: 筛选条件字典
            
        Returns:
            证书列表
        """
        with get_session() as session:
            query = select(Certificate)
            
            if filters:
                if "status" in filters:
                    query = query.where(Certificate.status == filters["status"])
                
                if "award_category" in filters:
                    query = query.where(Certificate.award_category == filters["award_category"])
                
                if "award_level" in filters:
                    query = query.where(Certificate.award_level == filters["award_level"])
                
                if "department" in filters:
                    query = query.where(Certificate.department == filters["department"])
            
            certificates = session.exec(query).all()
            return list(certificates)
    
    def delete_user(self, account_id: str) -> Tuple[bool, str]:
        """
        删除用户（及其相关数据）
        
        Args:
            account_id: 学（工）号
            
        Returns:
            (成功标志, 消息)
        """
        try:
            with get_session() as session:
                user = session.exec(
                    select(User).where(User.account_id == account_id)
                ).first()
                
                if not user:
                    return False, "用户不存在"
                
                # 删除用户的证书
                certs = session.exec(
                    select(Certificate).where(Certificate.submitter_id == user.user_id)
                ).all()
                for cert in certs:
                    session.delete(cert)
                
                # 删除用户的文件记录
                files = session.exec(
                    select(FileRecord).where(FileRecord.user_id == user.user_id)
                ).all()
                for file in files:
                    session.delete(file)
                
                # 删除用户
                session.delete(user)
                session.commit()
                
                return True, "用户及相关数据已删除"
        except Exception as e:
            return False, f"删除失败: {str(e)}"
