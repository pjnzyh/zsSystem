"""
用户认证模块
实现用户注册、登录、权限管理
"""
import hashlib
from typing import Optional, Tuple
from sqlmodel import Session, select
from models import User
from database import get_session, get_user_by_account_id, get_user_by_email
try:
    from utils import validate_account_id, validate_email, validate_password
except ImportError:
    # Streamlit Cloud路径修复
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from utils import validate_account_id, validate_email, validate_password


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def register_user(
    account_id: str,
    name: str,
    role: str,
    department: str,
    email: str,
    password: str
) -> Tuple[bool, str]:
    """
    用户注册
    
    Args:
        account_id: 学（工）号
        name: 姓名
        role: 角色（student/teacher）
        department: 单位/学院
        email: 邮箱
        password: 密码
        
    Returns:
        (成功标志, 消息)
    """
    # 验证学（工）号格式
    valid, msg = validate_account_id(account_id, role)
    if not valid:
        return False, msg
    
    # 验证邮箱格式
    if not validate_email(email):
        return False, "邮箱格式不正确"
    
    # 验证密码强度
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    
    # 检查账号是否已存在
    if get_user_by_account_id(account_id):
        return False, "该学（工）号已注册"
    
    # 检查邮箱是否已存在
    if get_user_by_email(email):
        return False, "该邮箱已被使用"
    
    # 创建用户
    try:
        with get_session() as session:
            user = User(
                account_id=account_id,
                name=name,
                role=role,
                department=department,
                email=email,
                password_hash=hash_password(password),
                created_by="self_register"
            )
            session.add(user)
            session.commit()
        
        return True, "注册成功！"
    except Exception as e:
        return False, f"注册失败: {str(e)}"


def login_user(account_id: str, password: str) -> Tuple[bool, Optional[User], str]:
    """
    用户登录
    
    Args:
        account_id: 学（工）号
        password: 密码
        
    Returns:
        (成功标志, 用户对象, 消息)
    """
    # 查找用户
    user = get_user_by_account_id(account_id)
    
    if not user:
        return False, None, "该学（工）号未注册，请先注册或联系管理员"
    
    # 检查账号是否被禁用
    if not user.is_active:
        return False, None, "账号已被禁用，请联系管理员"
    
    # 验证密码
    if not verify_password(password, user.password_hash):
        return False, None, "密码错误"
    
    return True, user, "登录成功！"


def check_permission(user: User, required_role: str) -> bool:
    """
    检查用户权限
    
    Args:
        user: 用户对象
        required_role: 所需角色（student/teacher/admin）
        
    Returns:
        是否有权限
    """
    role_hierarchy = {
        "student": 1,
        "teacher": 2,
        "admin": 3
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


def reset_password(account_id: str, new_password: str, admin_user_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    重置用户密码（管理员功能）
    
    Args:
        account_id: 学（工）号
        new_password: 新密码
        admin_user_id: 操作的管理员ID
        
    Returns:
        (成功标志, 消息)
    """
    # 验证密码强度
    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg
    
    try:
        with get_session() as session:
            user = session.exec(
                select(User).where(User.account_id == account_id)
            ).first()
            
            if not user:
                return False, "用户不存在"
            
            user.password_hash = hash_password(new_password)
            session.add(user)
            session.commit()
            
            return True, "密码重置成功"
    except Exception as e:
        return False, f"密码重置失败: {str(e)}"


def toggle_user_status(account_id: str, is_active: bool) -> Tuple[bool, str]:
    """
    启用/禁用用户账号（管理员功能）
    
    Args:
        account_id: 学（工）号
        is_active: 是否启用
        
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
            
            user.is_active = is_active
            session.add(user)
            session.commit()
            
            status_text = "启用" if is_active else "禁用"
            return True, f"账号已{status_text}"
    except Exception as e:
        return False, f"操作失败: {str(e)}"


def get_all_users(role_filter: Optional[str] = None) -> list:
    """
    获取所有用户列表（管理员功能）
    
    Args:
        role_filter: 角色筛选（student/teacher/admin），None表示不筛选
        
    Returns:
        用户列表
    """
    with get_session() as session:
        query = select(User)
        
        if role_filter:
            query = query.where(User.role == role_filter)
        
        users = session.exec(query).all()
        return list(users)


def update_user_info(
    account_id: str,
    name: Optional[str] = None,
    department: Optional[str] = None,
    email: Optional[str] = None
) -> Tuple[bool, str]:
    """
    更新用户信息
    
    Args:
        account_id: 学（工）号
        name: 新姓名
        department: 新单位
        email: 新邮箱
        
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
            
            if name:
                user.name = name
            
            if department:
                user.department = department
            
            if email:
                if not validate_email(email):
                    return False, "邮箱格式不正确"
                
                # 检查邮箱是否被其他用户使用
                existing = session.exec(
                    select(User).where(User.email == email, User.account_id != account_id)
                ).first()
                if existing:
                    return False, "该邮箱已被其他用户使用"
                
                user.email = email
            
            session.add(user)
            session.commit()
            
            return True, "信息更新成功"
    except Exception as e:
        return False, f"更新失败: {str(e)}"
