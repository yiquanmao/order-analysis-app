import streamlit as st
import PyPDF2
import io
import requests
import os
import re

# 检查pandas是否正确安装
try:
    import pandas as pd
    # 测试pandas是否可用
    test_df = pd.DataFrame({'test': [1, 2, 3]})
    if not isinstance(test_df, pd.DataFrame):
        raise ImportError("pandas DataFrame 不可用")
except ImportError as e:
    st.error(f"pandas模块未正确安装，请运行：pip install pandas==2.2.0")
    st.stop()
except Exception as e:
    st.error(f"pandas模块初始化失败：{str(e)}")
    st.stop()

# 设置页面配置
st.set_page_config(
    page_title="订单分析工具",
    page_icon="📊",
    layout="wide"
)

def get_api_key():
    """获取API密钥"""
    try:
        # 尝试从Streamlit Cloud的secrets获取
        return st.secrets["DEEPSEEK_API_KEY"]
    except:
        # 如果不在Streamlit Cloud上，尝试从环境变量获取
        return os.getenv("DEEPSEEK_API_KEY")

def extract_text_from_pdf(file):
    """从PDF文件中提取文本"""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def convert_to_csv(text):
    """将AI返回的文本转换为CSV格式"""
    try:
        # 分割成行
        lines = text.strip().split('\n')
        
        # 提取表头
        headers = []
        data = []
        
        # 找到表格开始的位置
        table_start = -1
        for i, line in enumerate(lines):
            if '|' in line and '客户单据序号' in line:
                table_start = i
                break
        
        if table_start == -1:
            st.error("未找到表格数据")
            return None
        
        # 提取表头
        header_line = lines[table_start]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # 提取数据行（跳过表头和分隔线）
        for line in lines[table_start + 2:]:
            if '|' in line:
                # 移除行首尾的|符号
                line = line.strip('|')
                # 分割单元格
                cells = [cell.strip() for cell in line.split('|')]
                if len(cells) == len(headers):
                    data.append(cells)
        
        if not data:
            st.error("未找到有效数据")
            return None
        
        # 创建DataFrame
        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        st.error(f"转换数据时出错：{str(e)}")
        st.write("原始文本：")
        st.write(text)
        return None

def analyze_order(content, file_type):
    """使用DeepSeek API分析订单内容"""
    api_key = get_api_key()
    if not api_key:
        st.error("请设置DEEPSEEK_API_KEY环境变量或secrets")
        return None
    
    prompt = f"""
    请分析以下{file_type}格式的订单内容，提取以下8个字段的信息：
    1. 客户单据序号
    2. 客户询价号
    3. 条目序号
    4. 物料编码
    5. 物料英文描述
    6. 数量
    7. 单位
    8. 中文（请根据物料英文描述生成对应的中文解释）

    请以Markdown表格形式返回结果，确保所有条目都被列出，不要遗漏任何信息。
    表格格式必须严格按照以下格式：
    | 客户单据序号 | 客户询价号 | 条目序号 | 物料编码 | 物料英文描述 | 数量 | 单位 | 中文 |
    |------------|------------|---------|---------|------------|------|------|------|
    | 数据1 | 数据2 | 数据3 | 数据4 | 数据5 | 数据6 | 数据7 | 数据8 |
    | ... | ... | ... | ... | ... | ... | ... | ... |

    注意：
    1. 表格必须包含表头和分隔线
    2. 每行数据必须包含8个字段
    3. 不要添加任何额外的说明文字
    4. 确保数据对齐
    
    订单内容：
    {content}
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            st.error(f"API调用失败: {response.text}")
            return None
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        return None

def main():
    st.title("订单分析工具")
    
    # 初始化session_state
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'dataframe' not in st.session_state:
        st.session_state.dataframe = None
    
    # 文件上传部分
    st.header("Input")
    uploaded_file = st.file_uploader("请上传订单文件（PDF/CSV/XLSX）", 
                                    type=['pdf', 'csv', 'xlsx'])
    
    if uploaded_file is not None:
        # 显示文件信息
        file_details = {"文件名": uploaded_file.name,
                       "文件类型": uploaded_file.type,
                       "文件大小": uploaded_file.size}
        st.write(file_details)
        
        # 分析按钮
        if st.button("Analysis"):
            with st.spinner("正在分析订单..."):
                try:
                    # 根据文件类型处理内容
                    if uploaded_file.type == "application/pdf":
                        content = extract_text_from_pdf(uploaded_file)
                        file_type = "PDF"
                    elif uploaded_file.type == "text/csv":
                        content = pd.read_csv(uploaded_file).to_string()
                        file_type = "CSV"
                    else:  # xlsx
                        content = pd.read_excel(uploaded_file).to_string()
                        file_type = "XLSX"
                    
                    # 分析内容
                    result = analyze_order(content, file_type)
                    
                    if result:
                        # 保存结果到session_state
                        st.session_state.analysis_result = result
                        # 转换为DataFrame并保存
                        st.session_state.dataframe = convert_to_csv(result)
                        
                except Exception as e:
                    st.error(f"分析过程中出现错误：{str(e)}")
    
    # 显示保存的结果
    if st.session_state.analysis_result:
        st.header("Output")
        st.write(st.session_state.analysis_result)
        
        # 导出按钮
        if st.session_state.dataframe is not None:
            try:
                # 使用StringIO创建内存中的CSV文件
                output = io.StringIO()
                # 添加BOM头
                output.write('\ufeff')
                # 导出DataFrame到CSV，使用UTF-8编码
                st.session_state.dataframe.to_csv(output, index=False, encoding='utf-8')
                # 获取CSV内容
                csv = output.getvalue()
                
                st.download_button(
                    label="导出为CSV",
                    data=csv,
                    file_name="order_analysis.csv",
                    mime="text/csv; charset=utf-8"
                )
            except Exception as e:
                st.error(f"导出CSV时出错：{str(e)}")

if __name__ == "__main__":
    main() 
