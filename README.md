# 竞赛证书智能识别与信息管理系统

## 系统简介

本系统是一个基于Streamlit框架开发的竞赛证书智能识别与信息管理平台，通过集成GLM-4V视觉识别API实现证书信息的自动提取，为学校或教育机构提供高效的证书信息采集和管理解决方案。

## 主要功能

### 1. 用户管理
- **三种角色**：学生（13位学号）、教师（8位工号）、管理员
- **用户注册**：支持在线自助注册
- **批量导入**：管理员可通过Excel批量导入用户信息
- **权限控制**：基于角色的访问控制(RBAC)

### 2. 证书处理
- **文件上传**：支持PDF、JPG、PNG等格式
- **智能识别**：调用GLM-4V API自动提取证书信息
- **信息核实**：用户可查看和修改识别结果
- **角色差异化**：
  - 学生：自动填充学号和姓名，需手动填写指导教师
  - 教师：自动填充指导教师，需填写学生信息

### 3. 管理员功能
- **数据统计**：用户数量、证书数量、按学院和获奖等级统计
- **用户管理**：查看、编辑、启用/禁用、重置密码、删除用户
- **数据导出**：支持导出为Excel或CSV格式
- **截止时间管理**：设置证书提交截止时间

## 快速开始

### 1. 安装依赖

```bash
cd zsSystem
pip install -r requirements.txt
```

### 2. 配置PDF支持（重要）

系统支持PDF格式证书上传，但需要先安装poppler工具。

#### Windows用户（推荐自动安装）

运行自动安装脚本：

```bash
python install_poppler.py
```

脚本会自动下载、安装并配置poppler。完成后重启命令行窗口。

#### Windows手动安装

1. 下载Poppler for Windows：
   - 访问：https://github.com/oschwartz10612/poppler-windows/releases
   - 下载最新的 Release-*.zip 文件

2. 解压到任意目录，例如：
   ```
   C:\Program Files\poppler
   ```

3. 添加bin目录到系统PATH：
   - 按 Win+R，输入 `sysdm.cpl`
   - 点击【高级】->【环境变量】
   - 在【系统变量】中找到 Path，点击【编辑】
   - 点击【新建】，添加路径（例如）：
     ```
     C:\Program Files\poppler\Library\bin
     ```
   - 点击【确定】保存
   - 重启命令行窗口

4. 验证安装：
   ```bash
   pdftoppm -v
   ```
   如果显示版本信息，说明安装成功。

#### Linux用户

```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

#### macOS用户

```bash
brew install poppler
```

#### 临时解决方案

如果暂时无法安装poppler，可以：
1. 使用在线工具将PDF转换为JPG/PNG格式
2. 上传转换后的图片文件

### 3. 初始化数据库

```bash
python database.py
```

这将创建数据库并生成默认管理员账号：
- 账号：admin001
- 密码：admin123

### 4. 启动系统

```bash
streamlit run app.py
```

系统将在浏览器中自动打开，默认地址：http://localhost:8501

## 使用指南

### 学生/教师用户

1. **注册账号**
   - 选择角色类型（学生/教师）
   - 填写学（工）号、姓名、单位、邮箱、密码
   - 提交注册

2. **上传证书**
   - 登录后进入"上传证书"标签页
   - 选择证书文件并上传
   - 系统自动识别证书信息
   - 核实并补充信息
   - 保存草稿或直接提交

3. **查看证书**
   - 在"我的证书"标签页查看已上传的证书
   - 可筛选草稿或已提交的证书

### 管理员用户

1. **批量导入用户**
   - 进入"用户管理"标签页
   - 使用Excel模板批量导入用户
   - Excel文件需包含：学（工）号、姓名、角色类型、单位、邮箱

2. **管理用户**
   - 查看所有用户列表
   - 启用/禁用账号
   - 重置用户密码
   - 删除用户

3. **导出数据**
   - 进入"证书管理"标签页
   - 可按状态、类别、等级筛选
   - 导出为Excel或CSV格式

4. **系统设置**
   - 设置证书提交截止时间
   - 截止后用户无法上传或修改

## 批量导入用户Excel模板

Excel文件应包含以下列：

| 学（工）号 | 姓名 | 角色类型 | 单位 | 邮箱 | 初始密码（可选） |
|----------|------|---------|------|------|---------------|
| 2024010101001 | 张三 | 学生 | 计算机学院 | zhangsan@example.com | 123456 |
| 20240101 | 李老师 | 教师 | 计算机学院 | lisi@example.com | 654321 |

注意：
- 学生学号必须为13位数字
- 教师工号必须为8位数字
- 角色类型：学生/student 或 教师/teacher
- 如不提供初始密码，系统自动生成：学（工）号@123

## 技术架构

- **前端框架**：Streamlit
- **数据库**：SQLite + SQLModel ORM
- **AI识别**：GLM-4V视觉模型API
- **数据验证**：Pydantic
- **文件处理**：PIL、pdf2image
- **数据导出**：Pandas、openpyxl

## 文件结构

```
zsSystem/
├── app.py                      # 主应用（Streamlit界面）
├── models.py                   # 数据模型定义
├── database.py                 # 数据库初始化和管理
├── auth.py                     # 用户认证模块
├── certificate_processor.py    # 证书处理模块
├── admin.py                    # 管理员功能模块
├── api_client.py              # API客户端（GLM-4V）
├── utils.py                   # 工具函数
├── config.py                  # 系统配置
├── requirements.txt           # 依赖包列表
├── README.md                  # 本文档
└── zsystem.db                 # SQLite数据库（运行后生成）
```

## 数据库表结构

### users（用户表）
- user_id：主键
- account_id：学（工）号（唯一）
- name：姓名
- role：角色（student/teacher/admin）
- department：单位/学院
- email：邮箱（唯一）
- password_hash：密码哈希
- is_active：账号状态
- created_at：注册时间
- created_by：创建方式

### certificates（证书信息表）
- cert_id：主键
- submitter_id：提交者ID
- submitter_role：提交者角色
- student_id：学号
- student_name：学生姓名
- department：学生所在学院
- competition_name：竞赛项目
- award_category：获奖类别
- award_level：获奖等级
- competition_type：竞赛类型
- organizer：主办单位
- award_date：获奖时间
- advisor：指导教师
- file_path：证书文件路径
- status：状态（draft/submitted）
- created_at：创建时间
- submitted_at：提交时间

### files（文件表）
- file_id：主键
- user_id：用户ID
- file_name：原始文件名
- file_path：服务器存储路径
- file_type：文件类型
- file_size：文件大小
- upload_time：上传时间

### system_config（系统配置表）
- config_id：主键
- config_key：配置键
- config_value：配置值
- description：配置说明
- updated_at：更新时间
- updated_by：更新者ID

## 注意事项

1. **API密钥**：请在config.py中配置您自己的GLM-4V API密钥
2. **文件存储**：上传的文件存储在uploads目录下，建议定期备份
3. **数据安全**：密码使用SHA-256哈希存储
4. **截止时间**：超过截止时间后，学生和教师无法上传或修改证书
5. **文件大小**：默认限制为10MB，可在config.py中修改

## 常见问题

### PDF文件上传问题

**Q: 上传PDF时报错"Poppler未安装或未配置到PATH"？**

A: 这是因为缺少poppler依赖。解决方法：

1. **自动安装（推荐）**：
   ```bash
   python install_poppler.py
   ```
   
2. **手动安装**：参考上面的"配置PDF支持"章节

3. **临时方案**：将PDF转换为图片格式（JPG/PNG）后上传

**Q: PDF转换失败，提示"无法读取PDF页数"？**

A: 可能的原因：
- PDF文件损坏 - 尝试重新下载或重新生成PDF
- PDF受密码保护 - 先解除密码保护
- PDF格式不兼容 - 使用Adobe Acrobat或其他工具重新保存

**Q: 为什么只支持PDF的第一页？**

A: 系统默认只处理证书的第一页（通常证书信息都在第一页）。如果需要处理多页，可以将每页保存为单独的PDF。

### 其他问题

**Q: 如何重置管理员密码？**

A: 删除zsystem.db文件，重新运行`python database.py`即可重新创建默认管理员账号。

**Q: 图片文件上传失败？**

A: 检查：
1. 文件格式是否为JPG/PNG/PDF
2. 文件大小是否超过10MB
3. 文件是否损坏（可以用图片查看器打开测试）

**Q: 如何修改API提供商？**

A: 在api_client.py中实现新的提取器类，并在config.py中配置。

**Q: 导出的Excel文件乱码怎么办？**

A: 使用Excel 2016或更高版本打开，或使用CSV格式导出。

## 开发信息

- 开发框架：Streamlit
- Python版本：3.8+
- 数据库：SQLite 3
- 许可证：MIT

## 更新日志

### v1.2.0 (2024-12-29)
- 修复：Streamlit Cloud部署时的模块导入问题
- 优化：在所有主要模块添加路径修复代码
- 测试：添加导入测试脚本验证模块加载
- 兼容：确保本地和云端环境都能正常运行

### v1.1.0 (2024-12-25)
- 新增：poppler自动安装脚本
- 优化：PDF转换错误处理和提示
- 修复：文件流消耗导致的上传失败问题
- 改进：增强了文件完整性验证

### v1.0.0 (2024-12-23)
- 初始版本发布
- 实现用户管理、证书处理、管理员功能
- 集成GLM-4V API进行证书智能识别
- 支持Excel批量导入用户
- 支持数据导出为Excel/CSV
