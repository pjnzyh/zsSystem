"""
API客户端模块
集成GLM-4V等视觉识别API
"""
import os
import sys
import base64
import json
import re
from typing import Dict, Optional, Tuple

# 修复Streamlit Cloud路径问题
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zhipuai import ZhipuAI


class CertificateExtractor:
    """证书信息提取器"""
    
    def __init__(self, api_key: str = "d2b1ea7220fa47c48847906ddd75302d.ikfmdiQVSgk9NLIo"):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4v-plus-0111"
    
    def extract_from_image(self, image_path: str) -> Tuple[bool, Dict, str]:
        """
        从图片中提取证书信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            (成功标志, 提取的数据字典, 错误信息)
        """
        try:
            # 转换为绝对路径
            abs_path = os.path.abspath(image_path)
            
            # 检查文件是否存在
            if not os.path.exists(abs_path):
                return False, {}, f"图片文件不存在: {abs_path}"
            
            # 检查文件大小
            if os.path.getsize(abs_path) == 0:
                return False, {}, f"图片文件为空: {abs_path}"
            
            # 读取图片并转换为Base64
            with open(abs_path, "rb") as img_file:
                img_base = base64.b64encode(img_file.read()).decode("utf-8")
            
            # 构造提示词
            prompt = self._build_extraction_prompt()
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": img_base
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # 解析响应
            result_text = response.choices[0].message.content
            
            # 提取结构化数据
            extracted_data = self._parse_response(result_text)
            
            return True, extracted_data, ""
            
        except FileNotFoundError as e:
            return False, {}, f"文件未找到: {str(e)}"
        except PermissionError as e:
            return False, {}, f"文件访问权限不足: {str(e)}"
        except Exception as e:
            return False, {}, f"API调用失败: {str(e)}"
    
    def _build_extraction_prompt(self) -> str:
        """构造提取信息的提示词"""
        prompt = """请仔细分析这张竞赛证书图片，提取以下信息：

1. 学生所在学院
2. 竞赛项目名称
3. 学号（13位数字）
4. 学生姓名
5. 获奖类别（国家级/省级）
6. 获奖等级（一等奖/二等奖/三等奖/金奖/银奖/铜奖/优秀奖等）
7. 竞赛类型（A类/B类）
8. 主办单位
9. 获奖时间（日期格式）
10. 指导教师姓名

请按照以下JSON格式返回结果，如果某个字段无法识别，请设置为null：

```json
{
    "department": "学院名称",
    "competition_name": "竞赛项目名称",
    "student_id": "13位学号",
    "student_name": "学生姓名",
    "award_category": "国家级或省级",
    "award_level": "获奖等级",
    "competition_type": "A类或B类",
    "organizer": "主办单位",
    "award_date": "获奖时间",
    "advisor": "指导教师"
}
```

请直接返回JSON，不要添加其他说明文字。"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        解析API返回的结果
        
        Args:
            response_text: API返回的文本
            
        Returns:
            提取的数据字典
        """
        # 初始化默认数据
        default_data = {
            "department": None,
            "competition_name": None,
            "student_id": None,
            "student_name": None,
            "award_category": None,
            "award_level": None,
            "competition_type": None,
            "organizer": None,
            "award_date": None,
            "advisor": None
        }
        
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 如果没有代码块标记，尝试直接解析
                json_str = response_text
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 合并数据（保留默认值）
            for key in default_data:
                if key in data and data[key]:
                    default_data[key] = data[key]
            
            return default_data
            
        except json.JSONDecodeError:
            # JSON解析失败，尝试正则表达式提取
            return self._parse_with_regex(response_text)
    
    def _parse_with_regex(self, text: str) -> Dict:
        """
        使用正则表达式从文本中提取信息
        
        Args:
            text: 原始文本
            
        Returns:
            提取的数据字典
        """
        data = {
            "department": None,
            "competition_name": None,
            "student_id": None,
            "student_name": None,
            "award_category": None,
            "award_level": None,
            "competition_type": None,
            "organizer": None,
            "award_date": None,
            "advisor": None
        }
        
        # 定义提取模式
        patterns = {
            "department": r'学院[：:]\s*([^\n,，]+)',
            "competition_name": r'竞赛[项目]*[名称]*[：:]\s*([^\n,，]+)',
            "student_id": r'学号[：:]\s*(\d{13})',
            "student_name": r'[学生]*姓名[：:]\s*([^\n,，]+)',
            "award_category": r'[获奖]*类别[：:]\s*(国家级|省级)',
            "award_level": r'[获奖]*等级[：:]\s*([一二三]等奖|[金银铜]奖|优秀奖)',
            "competition_type": r'[竞赛]*类型[：:]\s*([AB]类)',
            "organizer": r'主办[单位]*[：:]\s*([^\n,，]+)',
            "award_date": r'[获奖]*时间[：:]\s*(\d{4}[年-/]\d{1,2}[月-/]\d{1,2})',
            "advisor": r'指导教师[：:]\s*([^\n,，]+)'
        }
        
        # 逐个字段提取
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                data[field] = match.group(1).strip()
        
        return data


def test_api_connection(api_key: str) -> Tuple[bool, str]:
    """
    测试API连接
    
    Args:
        api_key: API密钥
        
    Returns:
        (成功标志, 消息)
    """
    try:
        client = ZhipuAI(api_key=api_key)
        # 发送一个简单的测试请求
        response = client.chat.completions.create(
            model="glm-4v-plus-0111",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "测试连接"
                        }
                    ]
                }
            ]
        )
        return True, "API连接成功"
    except Exception as e:
        return False, f"API连接失败: {str(e)}"


if __name__ == "__main__":
    # 测试代码
    extractor = CertificateExtractor()
    success, message = test_api_connection(extractor.api_key)
    print(f"测试结果: {message}")
