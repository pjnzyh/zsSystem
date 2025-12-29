"""
系统配置文件
"""

# 数据库配置
DATABASE_CONFIG = {
    "db_path": "zsystem.db",
    "echo": False
}

# 文件上传配置
UPLOAD_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".bmp"],
    "upload_dir": "uploads"
}

# API配置
API_CONFIG = {
    "glm4v": {
        "api_key": "d2b1ea7220fa47c48847906ddd75302d.ikfmdiQVSgk9NLIo",
        "model": "glm-4v-plus-0111"
    }
}

# 角色配置
ROLE_CONFIG = {
    "student": {
        "name": "学生",
        "account_id_length": 13,
        "permissions": ["upload_certificate", "view_own_certificates"]
    },
    "teacher": {
        "name": "教师",
        "account_id_length": 8,
        "permissions": ["upload_certificate", "view_own_certificates"]
    },
    "admin": {
        "name": "管理员",
        "account_id_length": None,
        "permissions": ["all"]
    }
}

# 证书字段配置
CERTIFICATE_FIELDS = {
    "department": "学生所在学院",
    "competition_name": "竞赛项目",
    "student_id": "学号",
    "student_name": "学生姓名",
    "award_category": "获奖类别",
    "award_level": "获奖等级",
    "competition_type": "竞赛类型",
    "organizer": "主办单位",
    "award_date": "获奖时间",
    "advisor": "指导教师"
}

# 获奖类别选项
AWARD_CATEGORIES = ["国家级", "省级"]

# 获奖等级选项
AWARD_LEVELS = ["一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"]

# 竞赛类型选项
COMPETITION_TYPES = ["A类", "B类"]

# 页面配置
PAGE_CONFIG = {
    "page_title": "竞赛证书管理系统",
    "page_icon": "🏆",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# 默认系统配置
DEFAULT_SYSTEM_CONFIG = {
    "submission_deadline": "2025-12-31 23:59:59",
    "api_provider": "glm4v",
    "max_file_size": "10485760"
}
