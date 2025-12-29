"""
数据库模型定义
使用 SQLModel 定义所有数据表结构
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """用户表"""
    __tablename__ = "users"
    
    user_id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(index=True, unique=True)  # 学（工）号
    name: str
    role: str  # student/teacher/admin
    department: str  # 单位/学院
    email: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = Field(default=True)  # 账号状态
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="self_register")  # self_register/admin_import


class Certificate(SQLModel, table=True):
    """证书信息表"""
    __tablename__ = "certificates"
    
    cert_id: Optional[int] = Field(default=None, primary_key=True)
    submitter_id: int = Field(foreign_key="users.user_id")  # 提交者ID
    submitter_role: str  # student/teacher
    student_id: str  # 学号（13位）
    student_name: str  # 学生姓名
    department: Optional[str] = None  # 学生所在学院
    competition_name: Optional[str] = None  # 竞赛项目
    award_category: Optional[str] = None  # 获奖类别（国家级、省级）
    award_level: Optional[str] = None  # 获奖等级
    competition_type: Optional[str] = None  # 竞赛类型（A类、B类）
    organizer: Optional[str] = None  # 主办单位
    award_date: Optional[str] = None  # 获奖时间
    advisor: str  # 指导教师
    file_path: str  # 证书文件路径
    extraction_method: Optional[str] = None  # 识别方式
    extraction_confidence: Optional[float] = None  # 识别置信度
    status: str = Field(default="draft")  # draft/submitted
    created_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None


class FileRecord(SQLModel, table=True):
    """文件表"""
    __tablename__ = "files"
    
    file_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    file_name: str  # 原始文件名
    file_path: str  # 服务器存储路径
    file_type: str  # pdf/image
    file_size: int  # 文件大小（字节）
    upload_time: datetime = Field(default_factory=datetime.now)


class SystemConfig(SQLModel, table=True):
    """系统配置表"""
    __tablename__ = "system_config"
    
    config_id: Optional[int] = Field(default=None, primary_key=True)
    config_key: str = Field(index=True, unique=True)
    config_value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
