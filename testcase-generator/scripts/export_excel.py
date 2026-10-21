# /// script
# dependencies = [
#   "openpyxl",
# ]
# ///
import argparse
import json
from pathlib import Path
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, PatternFill
from datetime import datetime

def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


class Args(argparse.Namespace):
    path: Path 


def export_excel(cases_json_path: Path, excel_file_path: str | Path):
    """读取 cases.json 并写入 excel"""

    # 解析 json 内容
    with open(cases_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "测试用例"

    # 定义表头
    headers = ["用例ID", "所属模块", "用例标题", "前置条件", "操作步骤", "预期结果"]

    # 表头样式
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 单元格样式
    cell_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    # 写入表头
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.alignment = header_alignment

    # 写入数据
    for row_num, case in enumerate(cases, 2):
        # ID
        cell = ws.cell(row=row_num, column=1)
        cell.value = case['id']
        cell.alignment = Alignment(horizontal="center", vertical="center")

        # 所属模块
        cell = ws.cell(row=row_num, column=2)
        cell.value = case['module']
        cell.alignment = Alignment(horizontal="center", vertical="center")

        # 标题
        cell = ws.cell(row=row_num, column=3)
        cell.value = case['title']
        cell.alignment = cell_alignment
        
        # 前置条件（列表转换为换行文本）
        cell = ws.cell(row=row_num, column=4)
        if case['preconditions']:
            preconditions_text = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(case['preconditions'])])
        else:
            preconditions_text = "无"
        cell.value = preconditions_text
        cell.alignment = cell_alignment
        
        # 操作步骤（列表转换为编号文本）
        cell = ws.cell(row=row_num, column=5)
        steps_text = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(case['steps'])])
        cell.value = steps_text
        cell.alignment = cell_alignment
        
        # 预期结果
        cell = ws.cell(row=row_num, column=6)
        cell.value = case['expected']
        cell.alignment = cell_alignment

    # 调整列宽
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 35
    ws.column_dimensions['D'].width = 40
    ws.column_dimensions['E'].width = 35

    # 设置行高（根据内容自适应）
    ws.row_dimensions[1].height = 25
    for row_num in range(2, len(cases) + 2):
        ws.row_dimensions[row_num].height = None  # 自动调整

    # 保存文件
    wb.save(excel_file_path)


def main():
    # 命令参数定义
    parser = argparse.ArgumentParser(description="解析 cases.json 并写入 excel")
    parser.add_argument("path", type=Path, help="cases.json 路径")
    args = parser.parse_args(namespace=Args())

    full_path = args.path.expanduser().resolve()
    # 路径校验
    if not full_path.exists():
        print(f"{full_path} 文件不存在")
        sys.exit(1)
    if not full_path.is_file():
        print(f"{full_path} 不是文件")
        sys.exit(1)
    if full_path.stat().st_size == 0:
        print(f"{full_path} 文件为空，大小 0 byte")
        sys.exit(1)

    excel_file_path = f"测试用例_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.xlsx"
    try:
        export_excel(cases_json_path=full_path, excel_file_path=excel_file_path)
        print(f"excel 文件生成成功: {str(Path(excel_file_path).expanduser().resolve())}")
        sys.exit(0)
    except Exception as e:
        print(f"excel 文件生成失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()