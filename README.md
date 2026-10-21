# skills

个人工作、学习产出的 skills 集合，主要是软件测试相关的 skill。


# testcase-generator

根据需求文档生成测试用例。

**1. 需求文档**

需求文档支持两种方式：
- 用户直接粘贴字符串
- 上传需求文档文件（支持 `.txt/.md/.word/.pdf`）


**2. 工作流程**

- 步骤1：获取需求
- 步骤2：分析需求
- 步骤3：设计测试用例
- 步骤4：写入 cases.json
- 步骤5：校验 cases.json
- 步骤6：导出用例
- 步骤7：总结

**3. 工具**

- `read_prd.py`：读取需求文件，使用的是 docling，需要下载几百 M 的模型依赖，可以自行二开改成其他文件解析库
- `validate_cases.py`：校验生成测试用例 cases.json 数据是否符合 cases-json.schema 定义
- `export_excel.py`：将测试用例写入 excel，使用 openpyxl
- `export_xmind.py`：将测试用例写入 xmind（teambiton 格式），可能存在版本兼容问题

