# /// script
# dependencies = [
#   "docling",
# ]
# ///
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


# 白名单格式，这些格式直接读取内容，不走 docling 解析，节约时间
WHITELIST_SUFFIXES = [".txt", ".md"]


def parse_whitelist(path: Path) -> tuple[bool, str]:
    """解析白名单格式文件"""
    text = path.read_text(encoding="utf-8")
    return text


def parse_with_docling(path: Path) -> tuple[bool, str]:
    """使用 docling 解析 docx 和 pdf 文档"""
    print("初次使用 docling 需要下载模型依赖库，正在下载中，请稍等片刻")
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(path.as_posix())
    return result.document.export_to_markdown()


def main():
    # 命令参数定义
    parser = argparse.ArgumentParser(description="读取需求文档，输出包含 markdown 格式的字符串文本")
    parser.add_argument("path", type=Path, help="需求文档路径")
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

    try:
        if full_path.suffix in WHITELIST_SUFFIXES:
            result = parse_whitelist(full_path)
        else:
            result = parse_with_docling(full_path)
        print(f"文件 {full_path} 解析成功")
        print(f"文件 {full_path} 解析结果: \n{result}")
        sys.exit(0)
    except Exception as e:
        print(f"脚本执行失败：{e}")
        sys.exit(1)

        
if __name__ == "__main__":
    main()