"""
竞赛证书管理系统 - 主应用
基于Streamlit框架开发
"""
import streamlit as st
import os
import sys
from datetime import datetime
from PIL import Image

# 修复Streamlit Cloud路径问题
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尝试导入poppler配置（如果存在）
try:
    import poppler_config
except ImportError:
    pass

# 导入自定义模块
from database import init_database, get_config, update_config
from auth import login_user, register_user, get_all_users, reset_password, toggle_user_status
from certificate_processor import CertificateProcessor
from admin import AdminManager
from config import (
    PAGE_CONFIG, AWARD_CATEGORIES, AWARD_LEVELS, 
    COMPETITION_TYPES, CERTIFICATE_FIELDS
)
from models import User


# 设置页面配置
st.set_page_config(**PAGE_CONFIG)


# 使用Streamlit缓存初始化数据库，避免重复初始化
@st.cache_resource
def initialize_database():
    """初始化数据库（仅执行一次）"""
    try:
        init_database()
        return True
    except Exception as e:
        st.error(f"数据库初始化失败: {str(e)}")
        return False

# 执行数据库初始化
initialize_database()


def init_session_state():
    """初始化会话状态"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'uploaded_file_path' not in st.session_state:
        st.session_state.uploaded_file_path = None
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = {}


def check_deadline() -> bool:
    """检查是否超过截止时间"""
    deadline_str = get_config("submission_deadline")
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
            return datetime.now() > deadline
        except:
            pass
    return False


def login_page():
    """登录页面"""
    st.title("🏆 竞赛证书管理系统")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("用户登录")
        
        account_id = st.text_input("学（工）号", key="login_account")
        password = st.text_input("密码", type="password", key="login_password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("登录", use_container_width=True):
                if not account_id or not password:
                    st.error("请输入学（工）号和密码")
                else:
                    success, user, message = login_user(account_id, password)
                    if success:
                        st.session_state.user = user
                        st.session_state.page = 'main'
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        with col_btn2:
            if st.button("注册", use_container_width=True):
                st.session_state.page = 'register'
                st.rerun()


def register_page():
    """注册页面"""
    st.title("🏆 竞赛证书管理系统")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("用户注册")
        
        role = st.selectbox("角色类型", ["学生", "教师"], key="reg_role")
        role_en = "student" if role == "学生" else "teacher"
        
        account_id_label = "学号（13位）" if role == "学生" else "工号（8位）"
        account_id = st.text_input(account_id_label, key="reg_account")
        
        name = st.text_input("姓名", key="reg_name")
        department = st.text_input("单位/学院", key="reg_dept")
        email = st.text_input("邮箱", key="reg_email")
        password = st.text_input("密码（至少8位，包含字母和数字）", type="password", key="reg_pass")
        password2 = st.text_input("确认密码", type="password", key="reg_pass2")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("注册", use_container_width=True):
                if not all([account_id, name, department, email, password, password2]):
                    st.error("请填写所有字段")
                elif password != password2:
                    st.error("两次密码输入不一致")
                else:
                    success, message = register_user(
                        account_id, name, role_en, department, email, password
                    )
                    if success:
                        st.success(message)
                        st.info("请返回登录")
                    else:
                        st.error(message)
        
        with col_btn2:
            if st.button("返回登录", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()


def student_teacher_page(user: User):
    """学生/教师功能页面"""
    st.title(f"欢迎，{user.name}（{user.role == 'student' and '学生' or '教师'}）")
    
    # 检查截止时间
    is_deadline_passed = check_deadline()
    if is_deadline_passed:
        st.warning("⚠️ 证书提交截止时间已过，无法上传或修改证书")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📤 上传证书", "📋 我的证书", "👤 个人信息"])
    
    # 标签页1：上传证书
    with tab1:
        if is_deadline_passed:
            st.error("提交截止时间已过")
        else:
            upload_certificate_section(user)
    
    # 标签页2：我的证书
    with tab2:
        my_certificates_section(user)
    
    # 标签页3：个人信息
    with tab3:
        user_profile_section(user)


def upload_certificate_section(user: User):
    """上传证书部分"""
    st.subheader("上传证书文件")
    
    # PDF支持提示
    with st.expander("💡 PDF文件上传说明"):
        st.markdown("""
        系统支持PDF格式证书，但需要先安装poppler工具。
        
        **如果遇到PDF上传错误：**
        1. 运行: `python install_poppler.py`（自动安装）
        2. 或参考：`PDF支持配置指南.md`（手动安装）
        3. 临时方案：将PDF转换为JPG/PNG格式后上传
        
        **支持的格式：** PDF, JPG, PNG, BMP（最大10MB）
        """)
    
    processor = CertificateProcessor(user)
    
    uploaded_file = st.file_uploader(
        "选择证书文件（PDF或图片格式，最大10MB）",
        type=['pdf', 'jpg', 'jpeg', 'png', 'bmp']
    )
    
    if uploaded_file:
        # 显示文件预览
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 证书预览")
            try:
                if uploaded_file.type == "application/pdf":
                    st.info("PDF文件已上传，点击'提取信息'进行识别")
                else:
                    # 重要：需要先seek(0)重置文件指针，或者使用getvalue()
                    # 使用BytesIO来避免消耗原始文件流
                    from io import BytesIO
                    image_bytes = BytesIO(uploaded_file.getvalue())
                    image = Image.open(image_bytes)
                    st.image(image, use_container_width=True)
            except Exception as e:
                st.error(f"文件预览失败: {str(e)}")
        
        with col2:
            st.markdown("### 操作")
            
            if st.button("📥 上传并提取信息", use_container_width=True):
                # 确保文件指针在开始位置
                uploaded_file.seek(0)
                
                with st.spinner("正在上传文件..."):
                    success, file_path, message = processor.upload_file(uploaded_file)
                    
                    if success:
                        st.success(message)
                        st.session_state.uploaded_file_path = file_path
                        
                        # 提取信息
                        with st.spinner("正在识别证书信息，请稍候..."):
                            success, data, msg = processor.extract_certificate_info(file_path)
                            
                            if success:
                                st.success(msg)
                                st.session_state.extracted_data = data
                                st.rerun()
                            else:
                                st.error(msg)
                                st.info("您可以手动填写证书信息")
                                st.session_state.extracted_data = {}
                    else:
                        st.error(message)
    
    # 显示提取的信息表单
    if st.session_state.get('extracted_data') or st.session_state.get('uploaded_file_path'):
        st.markdown("---")
        st.subheader("证书信息确认")
        
        data = st.session_state.get('extracted_data', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            department = st.text_input(
                "学生所在学院",
                value=data.get('department', ''),
                key="cert_dept"
            )
            
            competition_name = st.text_input(
                "竞赛项目",
                value=data.get('competition_name', ''),
                key="cert_comp"
            )
            
            # 根据角色设置学号和姓名
            if user.role == "student":
                student_id = st.text_input(
                    "学号（自动填充，不可修改）",
                    value=user.account_id,
                    disabled=True,
                    key="cert_sid"
                )
                student_name = st.text_input(
                    "学生姓名（自动填充，不可修改）",
                    value=user.name,
                    disabled=True,
                    key="cert_sname"
                )
            else:
                student_id = st.text_input(
                    "学号（13位）",
                    value=data.get('student_id', ''),
                    key="cert_sid"
                )
                student_name = st.text_input(
                    "学生姓名",
                    value=data.get('student_name', ''),
                    key="cert_sname"
                )
            
            award_category = st.selectbox(
                "获奖类别",
                [""] + AWARD_CATEGORIES,
                index=AWARD_CATEGORIES.index(data.get('award_category', '')) + 1 if data.get('award_category') in AWARD_CATEGORIES else 0,
                key="cert_category"
            )
            
            award_level = st.selectbox(
                "获奖等级",
                [""] + AWARD_LEVELS,
                index=AWARD_LEVELS.index(data.get('award_level', '')) + 1 if data.get('award_level') in AWARD_LEVELS else 0,
                key="cert_level"
            )
        
        with col2:
            competition_type = st.selectbox(
                "竞赛类型",
                [""] + COMPETITION_TYPES,
                index=COMPETITION_TYPES.index(data.get('competition_type', '')) + 1 if data.get('competition_type') in COMPETITION_TYPES else 0,
                key="cert_type"
            )
            
            organizer = st.text_input(
                "主办单位",
                value=data.get('organizer', ''),
                key="cert_org"
            )
            
            award_date = st.text_input(
                "获奖时间（YYYY-MM-DD）",
                value=data.get('award_date', ''),
                key="cert_date"
            )
            
            # 根据角色设置指导教师
            if user.role == "teacher":
                advisor = st.text_input(
                    "指导教师（自动填充，不可修改）",
                    value=user.name,
                    disabled=True,
                    key="cert_advisor"
                )
            else:
                advisor = st.text_input(
                    "指导教师",
                    value=data.get('advisor', ''),
                    key="cert_advisor"
                )
        
        # 提交按钮
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("💾 保存草稿", use_container_width=True):
                cert_data = {
                    "department": department,
                    "competition_name": competition_name,
                    "student_id": student_id,
                    "student_name": student_name,
                    "award_category": award_category if award_category else None,
                    "award_level": award_level if award_level else None,
                    "competition_type": competition_type if competition_type else None,
                    "organizer": organizer,
                    "award_date": award_date,
                    "advisor": advisor
                }
                
                success, cert_id, message = processor.save_draft(
                    st.session_state.uploaded_file_path,
                    cert_data
                )
                
                if success:
                    st.success(message)
                    # 清空状态
                    st.session_state.uploaded_file_path = None
                    st.session_state.extracted_data = {}
                    st.rerun()
                else:
                    st.error(message)
        
        with col_btn2:
            if st.button("✅ 提交", use_container_width=True):
                cert_data = {
                    "department": department,
                    "competition_name": competition_name,
                    "student_id": student_id,
                    "student_name": student_name,
                    "award_category": award_category if award_category else None,
                    "award_level": award_level if award_level else None,
                    "competition_type": competition_type if competition_type else None,
                    "organizer": organizer,
                    "award_date": award_date,
                    "advisor": advisor
                }
                
                success, message = processor.submit_certificate(
                    cert_data,
                    st.session_state.uploaded_file_path
                )
                
                if success:
                    st.success(message)
                    # 清空状态
                    st.session_state.uploaded_file_path = None
                    st.session_state.extracted_data = {}
                    st.rerun()
                else:
                    st.error(message)


def my_certificates_section(user: User):
    """我的证书部分"""
    st.subheader("我的证书列表")
    
    processor = CertificateProcessor(user)
    
    # 状态筛选
    status_filter = st.selectbox(
        "筛选状态",
        ["全部", "草稿", "已提交"],
        key="my_cert_filter"
    )
    
    status_map = {"全部": None, "草稿": "draft", "已提交": "submitted"}
    certificates = processor.get_my_certificates(status_map[status_filter])
    
    if not certificates:
        st.info("暂无证书记录")
    else:
        for cert in certificates:
            with st.expander(
                f"{'📝' if cert.status == 'draft' else '✅'} {cert.competition_name or '未命名'} - {cert.student_name} ({cert.status == 'draft' and '草稿' or '已提交'})"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**学号**: {cert.student_id}")
                    st.write(f"**学生姓名**: {cert.student_name}")
                    st.write(f"**学院**: {cert.department or '未填写'}")
                    st.write(f"**竞赛项目**: {cert.competition_name or '未填写'}")
                    st.write(f"**获奖类别**: {cert.award_category or '未填写'}")
                
                with col2:
                    st.write(f"**获奖等级**: {cert.award_level or '未填写'}")
                    st.write(f"**竞赛类型**: {cert.competition_type or '未填写'}")
                    st.write(f"**主办单位**: {cert.organizer or '未填写'}")
                    st.write(f"**获奖时间**: {cert.award_date or '未填写'}")
                    st.write(f"**指导教师**: {cert.advisor}")
                
                st.write(f"**创建时间**: {cert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if cert.submitted_at:
                    st.write(f"**提交时间**: {cert.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 显示证书图片
                if os.path.exists(cert.file_path):
                    try:
                        if cert.file_path.endswith('.pdf'):
                            st.info("PDF文件")
                        else:
                            image = Image.open(cert.file_path)
                            st.image(image, caption="证书图片", use_container_width=True)
                    except:
                        st.warning("无法显示证书文件")


def user_profile_section(user: User):
    """个人信息部分"""
    st.subheader("个人信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**学（工）号**: {user.account_id}")
        st.write(f"**姓名**: {user.name}")
        st.write(f"**角色**: {user.role == 'student' and '学生' or '教师'}")
    
    with col2:
        st.write(f"**单位/学院**: {user.department}")
        st.write(f"**邮箱**: {user.email}")
        st.write(f"**注册时间**: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


def admin_page(user: User):
    """管理员功能页面"""
    st.title(f"管理员控制台 - {user.name}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 统计概览", "👥 用户管理", "📋 证书管理", "⚙️ 系统设置"])
    
    admin_mgr = AdminManager(user)
    
    # 标签页1：统计概览
    with tab1:
        statistics_section(admin_mgr)
    
    # 标签页2：用户管理
    with tab2:
        user_management_section(admin_mgr)
    
    # 标签页3：证书管理
    with tab3:
        certificate_management_section(admin_mgr)
    
    # 标签页4：系统设置
    with tab4:
        system_settings_section(user)


def statistics_section(admin_mgr: AdminManager):
    """统计概览部分"""
    st.subheader("系统统计")
    
    stats = admin_mgr.get_statistics()
    
    # 用户统计
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总用户数", stats['user_total'])
    col2.metric("学生数", stats['student_count'])
    col3.metric("教师数", stats['teacher_count'])
    col4.metric("管理员数", stats['admin_count'])
    
    st.markdown("---")
    
    # 证书统计
    col1, col2, col3 = st.columns(3)
    col1.metric("证书总数", stats['cert_total'])
    col2.metric("已提交", stats['cert_submitted'])
    col3.metric("草稿", stats['cert_draft'])
    
    st.markdown("---")
    
    # 按学院统计
    if stats['dept_stats']:
        st.subheader("各学院证书提交情况")
        import pandas as pd
        dept_df = pd.DataFrame(
            list(stats['dept_stats'].items()),
            columns=['学院', '证书数量']
        )
        st.dataframe(dept_df, use_container_width=True)
    
    # 按获奖等级统计
    if stats['award_stats']:
        st.subheader("获奖等级分布")
        import pandas as pd
        award_df = pd.DataFrame(
            list(stats['award_stats'].items()),
            columns=['获奖等级', '数量']
        )
        st.dataframe(award_df, use_container_width=True)


def user_management_section(admin_mgr: AdminManager):
    """用户管理部分"""
    st.subheader("用户管理")
    
    # 批量导入
    with st.expander("📥 批量导入用户"):
        st.write("上传Excel文件批量导入用户（需包含：学（工）号、姓名、角色类型、单位、邮箱）")
        
        uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'], key="import_users")
        
        if uploaded_file and st.button("开始导入"):
            with st.spinner("正在导入..."):
                success, stats, message = admin_mgr.import_users_from_excel(uploaded_file)
                
                if success:
                    st.success(message)
                    if stats.get('errors'):
                        with st.expander("查看详细错误"):
                            for error in stats['errors']:
                                st.text(error)
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # 用户列表
    role_filter = st.selectbox("角色筛选", ["全部", "学生", "教师", "管理员"], key="user_role_filter")
    
    role_map = {"全部": None, "学生": "student", "教师": "teacher", "管理员": "admin"}
    users = get_all_users(role_map[role_filter])
    
    if users:
        for u in users:
            with st.expander(f"{u.name} ({u.account_id}) - {u.role}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**学（工）号**: {u.account_id}")
                    st.write(f"**姓名**: {u.name}")
                    st.write(f"**角色**: {u.role}")
                    st.write(f"**单位**: {u.department}")
                
                with col2:
                    st.write(f"**邮箱**: {u.email}")
                    st.write(f"**状态**: {'启用' if u.is_active else '禁用'}")
                    st.write(f"**创建方式**: {u.created_by}")
                    st.write(f"**注册时间**: {u.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 操作按钮
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button(f"{'禁用' if u.is_active else '启用'}", key=f"toggle_{u.user_id}"):
                        success, msg = toggle_user_status(u.account_id, not u.is_active)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                
                with col_btn2:
                    if st.button("重置密码", key=f"reset_{u.user_id}"):
                        new_pass = f"{u.account_id}@123"
                        success, msg = reset_password(u.account_id, new_pass)
                        if success:
                            st.success(f"{msg}（新密码：{new_pass}）")
                        else:
                            st.error(msg)
                
                with col_btn3:
                    if st.button("删除用户", key=f"del_{u.user_id}"):
                        success, msg = admin_mgr.delete_user(u.account_id)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        st.info("暂无用户")


def certificate_management_section(admin_mgr: AdminManager):
    """证书管理部分"""
    st.subheader("证书数据管理")
    
    # 导出功能
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 导出为Excel", use_container_width=True):
            with st.spinner("正在导出..."):
                success, file_path, message = admin_mgr.export_certificates_to_excel()
                
                if success:
                    st.success(message)
                    
                    # 提供下载
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 下载Excel文件",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(message)
    
    with col2:
        if st.button("📄 导出为CSV", use_container_width=True):
            with st.spinner("正在导出..."):
                success, file_path, message = admin_mgr.export_certificates_to_csv()
                
                if success:
                    st.success(message)
                    
                    # 提供下载
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 下载CSV文件",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="text/csv"
                        )
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # 证书列表
    st.subheader("证书列表")
    
    # 筛选
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态", ["全部", "已提交", "草稿"], key="cert_status_filter")
    with col2:
        category_filter = st.selectbox("获奖类别", ["全部"] + AWARD_CATEGORIES, key="cert_cat_filter")
    with col3:
        level_filter = st.selectbox("获奖等级", ["全部"] + AWARD_LEVELS, key="cert_level_filter")
    
    filters = {}
    if status_filter != "全部":
        filters['status'] = "submitted" if status_filter == "已提交" else "draft"
    if category_filter != "全部":
        filters['award_category'] = category_filter
    if level_filter != "全部":
        filters['award_level'] = level_filter
    
    certificates = admin_mgr.get_all_certificates(filters)
    
    st.write(f"共 {len(certificates)} 条记录")
    
    if certificates:
        import pandas as pd
        cert_data = []
        for cert in certificates:
            cert_data.append({
                "证书ID": cert.cert_id,
                "学号": cert.student_id,
                "学生姓名": cert.student_name,
                "竞赛项目": cert.competition_name or "",
                "获奖类别": cert.award_category or "",
                "获奖等级": cert.award_level or "",
                "指导教师": cert.advisor,
                "状态": "已提交" if cert.status == "submitted" else "草稿",
                "提交时间": cert.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if cert.submitted_at else ""
            })
        
        df = pd.DataFrame(cert_data)
        st.dataframe(df, use_container_width=True)


def system_settings_section(user: User):
    """系统设置部分"""
    st.subheader("系统设置")
    
    # 截止时间设置
    st.markdown("### 提交截止时间")
    
    current_deadline = get_config("submission_deadline")
    
    if current_deadline:
        try:
            deadline_dt = datetime.strptime(current_deadline, "%Y-%m-%d %H:%M:%S")
            st.write(f"当前截止时间：**{current_deadline}**")
        except:
            deadline_dt = datetime.now()
    else:
        deadline_dt = datetime.now()
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_date = st.date_input("新截止日期", value=deadline_dt.date())
    
    with col2:
        new_time = st.time_input("新截止时间", value=deadline_dt.time())
    
    if st.button("更新截止时间"):
        new_deadline = f"{new_date} {new_time}"
        update_config("submission_deadline", new_deadline, user.user_id)
        st.success(f"截止时间已更新为：{new_deadline}")
        st.rerun()


def main():
    """主函数"""
    # 初始化数据库
    if not os.path.exists("zsystem.db"):
        init_database()
    
    # 初始化会话状态
    init_session_state()
    
    # 侧边栏
    with st.sidebar:
        st.title("🏆 证书管理系统")
        
        if st.session_state.user:
            st.write(f"**当前用户**: {st.session_state.user.name}")
            st.write(f"**角色**: {st.session_state.user.role}")
            st.write(f"**学（工）号**: {st.session_state.user.account_id}")
            
            st.markdown("---")
            
            if st.button("🚪 退出登录", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = 'login'
                st.session_state.uploaded_file_path = None
                st.session_state.extracted_data = {}
                st.rerun()
        else:
            st.info("请登录系统")
    
    # 主页面路由
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'main':
        if st.session_state.user:
            if st.session_state.user.role == 'admin':
                admin_page(st.session_state.user)
            else:
                student_teacher_page(st.session_state.user)
        else:
            st.session_state.page = 'login'
            st.rerun()


if __name__ == "__main__":
    main()
