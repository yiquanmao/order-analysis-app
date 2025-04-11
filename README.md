# 订单分析工具

这是一个基于Streamlit开发的订单分析工具，可以处理PDF、CSV和XLSX格式的订单文件，并使用DeepSeek API进行智能分析。

## 功能特点

- 支持多种文件格式：PDF、CSV、XLSX
- 自动提取8个关键字段信息：
  - 客户单据序号
  - 客户询价号
  - 条目序号
  - 物料编码
  - 物料英文描述
  - 数量
  - 单位
  - 中文（自动生成）
- 支持结果导出为CSV文件
- 完整的条目展示，无遗漏

## 部署说明

### Streamlit Cloud 部署
1. 将代码上传到 GitHub 仓库
2. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
3. 使用 GitHub 账号登录
4. 创建新应用并连接仓库
5. 在应用设置中添加环境变量：
   ```
   DEEPSEEK_API_KEY=您的API密钥
   ```
6. 点击部署按钮

## 使用方法

1. 访问部署后的应用链接
2. 上传订单文件
3. 点击"Analysis"按钮进行分析
4. 查看分析结果并选择导出为CSV文件

## 注意事项

- 确保上传的文件格式正确
- 分析过程可能需要一些时间，请耐心等待
- 建议使用Chrome或Edge浏览器访问应用
- 确保已正确设置DeepSeek API密钥 