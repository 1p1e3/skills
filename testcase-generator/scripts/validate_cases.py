import json
from pathlib import Path
import sys
import argparse

def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

class Args(argparse.Namespace):
    path: Path 


# 必填字段
REQUIRED_FIELD = ("title", "module", "preconditions", "steps", "expected")

def check_case(case, index, errors: list, warnings: list):
    """检查单条用例"""

    # 第几条用例，以索引顺序标识
    loc = f"case[{index}]"

    # 1. 根据 cases_schema.json 定义，每条 case 整体是一个对象，python 中是 dict
    if not isinstance(case, dict):
        errors.append(("error", loc, f"用例应为对象，实际为 {type(case).__name__}"))
        return

    # 如果 id 是数字类型，则将 id 插入 loc，更好辨认
    if isinstance(case.get("id"), int) and not isinstance(case.get("id"), bool):
        loc = f"{loc} id={case['id']}"

    # 2. id 的校验
    if "id" not in case:
        errors.append(("error", loc, "缺少必填字段 id"))
    elif not (isinstance(case.get("id"), int) and not isinstance(case.get("id"), bool)):
        errors.append(("error", loc, f"id 应为整数，实际是 {type(case.get("id")).__name__}"))
    elif case.get("id") <= 0:
        errors.append(("error", loc, f"id 应为正整数，实际是 {case.get("id")}"))

    # 3. 其他必填字符串校验
    for field in REQUIRED_FIELD:
        if field not in case:
            errors.append(("error", loc, f"缺少必填字段 {field}"))
        elif isinstance(case[field], str) and not case[field].strip():
            errors.append(("error", loc, f"{field} 值为空"))

    # 4. title 字段校验
    title = case.get("title")
    if not isinstance(title, str):
        errors.append(("error", loc, f"title 字段类型应为字符串，实际是 {type(title).__name__}"))
    elif len(title) < 10:
        errors.append(("error", loc, f"title 太短，最少要 10 个字符"))

    # 所属模块校验
    module = case.get("module")
    if not isinstance(module, str):
        errors.append(("error", loc, f"module 字段类型应为字符串，实际是 {type(module).__name__}"))
    elif len(module) < 2:
        errors.append(("error", loc, f"module 字段值太短，最少要 2 个字符"))

    # 5. preconditions 字段校验
    preconditions = case.get("preconditions")
    if not isinstance(preconditions, list):
        errors.append(("error", loc, f"preconditions 字段类型应为数组，实际是 {type(preconditions).__name__}"))

    # 6. preconditions 字段校验
    steps = case.get("steps")
    if not isinstance(steps, list):
        errors.append(("error", loc, f"steps 字段类型应为数组，实际是 {type(steps).__name__}"))

    # 7. expected 字段校验
        expected = case.get("expected")
        if not isinstance(expected, str):
            errors.append(("error", loc, f"expected 字段类型应为字符串，实际是 {type(expected).__name__}"))
        elif len(expected) < 5:
            errors.append(("error", loc, f"expected 太短，最少要 5 个字符"))

    # 8. 未知字段
    for field in case:
        if field != "id" and field not in REQUIRED_FIELD:
            warnings.append(("warning", loc, f"出现多余字段 {field}"))


def validate(data):
    """整体校验"""

    errors, warnings = [], []

    # 1. 顶层必须是对象
    if not isinstance(data, dict):
        errors.append(("error", "json 最外层", f"顶层应为对象，实际是 {type(data).__name__}"))
        return errors, warnings

    # 2. cases 字段不存在
    if  "cases" not in data:
        errors.append(("error", "json 最外层", "缺少顶层用例数组字段 cases"))
        return errors, warnings

    # 3. cases 字段类型不为数组
    cases = data["cases"]
    if not isinstance(cases, list):
        errors.append(("error", "json 最外层", "顶层字段 cases 类型应为数组"))
        return errors, warnings

    # 4. 用例数组为空
    if not cases:
        errors.append(("error", "json 最外层", "cases 用例数组不能为空，至少要有一条用例"))

    # 5. 检查单条用例
    for index, case in enumerate(cases):
        check_case(case=case, index=index, errors=errors, warnings=warnings)

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="校验 cases.json 是否合规")
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

    # 读取 cases.json
    try:
        raw = args.path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"读取 cases.json 失败：{e}")
        sys.exit(1)

    # 将原始字符串解析为 dict
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"cases.json 原始字符串转换失败：{e}")

        sys.exit(1)
    try:
        errors, warnings = validate(data)
    except Exception as e:
        print(f"cases.json 校验失败，脚本异常: {e}")

        sys.exit(1)
    if errors:
        print(f"casess.json 校验失败，存在不符合 schema 定义和约束的数据：{errors}")
        sys.exit(1)
    
    if warnings:
        print("casess.json 存在未声明或不需要的字段")
        sys.exit(1)

    print(f"{len(data['cases'])} 条测试用例全部校验通过")
    sys.exit(0)
        

if __name__ == "__main__":
    main()