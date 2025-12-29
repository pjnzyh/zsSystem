"""
数据库初始化和管理
"""
import sys
import os

# 修复Streamlit Cloud路径问题
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import SQLModel, create_engine, Session, select
from typing import Optional, TYPE_CHECKING
from datetime import datetime

# 使用TYPE_CHECKING避免运行时导入，仅用于类型检查
if TYPE_CHECKING:
    from models import User, Certificate, FileRecord, SystemConfig

# 数据库文件路径
DB_PATH = "zsystem.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建数据库引擎（使用单例模式）
_engine = None

def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL, 
            echo=False, 
            connect_args={"check_same_thread": False},
            poolclass=None  # 禁用连接池，避免Streamlit重载问题
        )
    return _engine

engine = get_engine()


def init_database():
    """初始化数据库，创建所有表"""
    from models import User, SystemConfig
    
    # 使用 checkfirst=True 避免重复创建表
    SQLModel.metadata.create_all(engine, checkfirst=True)
    print("数据库初始化完成")
    
    # 创建默认管理员账号
    with Session(engine) as session:
        # 检查是否已存在管理员
        existing_admin = session.exec(
            select(User).where(User.role == "admin")
        ).first()
        
        if not existing_admin:
            from auth import hash_password
            admin = User(
                account_id="admin001",
                name="系统管理员",
                role="admin",
                department="教务处",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                created_by="system"
            )
            session.add(admin)
            
            # 创建默认系统配置
            default_configs = [
                SystemConfig(
                    config_key="submission_deadline",
                    config_value="2025-12-31 23:59:59",
                    description="证书提交截止时间"
                ),
                SystemConfig(
                    config_key="api_provider",
                    config_value="glm4v",
                    description="默认API提供商"
                ),
                SystemConfig(
                    config_key="max_file_size",
                    config_value="10485760",
                    description="最大文件大小（字节）"
                )
            ]
            for config in default_configs:
                session.add(config)
            
            session.commit()
            print("默认管理员账号已创建（账号：admin001，密码：admin123）")


def get_session():
    """获取数据库会话"""
    return Session(engine)


def get_user_by_account_id(account_id: str) -> Optional["User"]:
    """根据学（工）号获取用户"""
    from models import User
    with get_session() as session:
        user = session.exec(
            select(User).where(User.account_id == account_id)
        ).first()
        return user


def get_user_by_email(email: str) -> Optional["User"]:
    """根据邮箱获取用户"""
    from models import User
    with get_session() as session:
        user = session.exec(
            select(User).where(User.email == email)
        ).first()
        return user


def get_config(key: str) -> Optional[str]:
    """获取系统配置"""
    from models import SystemConfig
    with get_session() as session:
        config = session.exec(
            select(SystemConfig).where(SystemConfig.config_key == key)
        ).first()
        return config.config_value if config else None


def update_config(key: str, value: str, user_id: Optional[int] = None):
    """更新系统配置"""
    from models import SystemConfig
    with get_session() as session:
        config = session.exec(
            select(SystemConfig).where(SystemConfig.config_key == key)
        ).first()
        
        if config:
            config.config_value = value
            config.updated_at = datetime.now()
            config.updated_by = user_id
        else:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                updated_by=user_id
            )
            session.add(config)
        
        session.commit()


if __name__ == "__main__":
    init_database()
