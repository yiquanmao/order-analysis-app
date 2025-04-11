import streamlit as st
import pandas as pd
import PyPDF2
import io
import requests
import os

# 设置页面配置
st.set_page_config(
    page_title="订单分析工具",
    page_icon="📊",
    layout="wide"
)

def extract_text_from_pdf(file):
    """从PDF文件中提取文本"""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def analyze_order(content, file_type):
    """使用DeepSeek API分析订单内容"""
    api_key = st.secrets["DEEPSEEK_API_KEY"]
    if not api_key:
        st.error("请在Streamlit Cloud中设置DEEPSEEK_API_KEY")
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

    请以表格形式返回结果，确保所有条目都被列出，不要遗漏任何信息。
    
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
                        # 显示结果
                        st.header("Output")
                        st.write(result)
                        
                        # 导出按钮
                        if st.button("导出为CSV"):
                            # 将结果转换为DataFrame
                            df = pd.read_csv(io.StringIO(result))
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="下载CSV文件",
                                data=csv,
                                file_name="order_analysis.csv",
                                mime="text/csv"
                            )
                        
                except Exception as e:
                    st.error(f"分析过程中出现错误：{str(e)}")

if __name__ == "__main__":
    main() 