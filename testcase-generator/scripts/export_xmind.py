# /// script
# dependencies = [
#   "xmind",
# ]
# ///
import argparse
import json
import uuid
import zipfile
from pathlib import Path
import sys
from datetime import datetime
import xmind
from xmind.core.markerref import MarkerId

def force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


class Args(argparse.Namespace):
    path: Path 


def export_xmind(cases_json_path, xmind_file_path):
    """
    将测试用例 JSON 文件转换为 XMind 思维导图
    
    结构层级(teambition 格式)：
    - 根主题：测试用例
    - 二级主题：所属模块
    - 三级主题：tc: 用例标题
    - 四级主题：pc: 前置条件 / 操作步骤
    - 五级主题：具体步骤内容
    - 六级主题：预期结果
    """
    # 读取 JSON 数据
    with open(cases_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data["cases"]
    
    # 创建 XMind 工作簿
    workbook = xmind.load(xmind_file_path)
    sheet = workbook.getPrimarySheet()
    
    # 设置根主题
    root_topic = sheet.getRootTopic()
    root_topic.setTitle("测试用例")
    
    # 按模块分组
    modules = {}
    for case in cases:
        module_name = case['module']
        if module_name not in modules:
            modules[module_name] = []
        modules[module_name].append(case)
    
    # 为每个模块创建二级主题
    for module_name, module_cases in modules.items():
        # 创建模块主题（二级）
        module_topic = root_topic.addSubTopic()
        module_topic.setTitle(module_name)
        
        # 为每个用例创建三级主题
        for case in module_cases:
            # 三级：用例标题（加 tc: 前缀）
            case_topic = module_topic.addSubTopic()
            case_topic.setTitle(f"tc: {case['title']}")
            
            # 四级：前置条件（如果有）
            if case['preconditions']:
                preconditions_topic = case_topic.addSubTopic()
                preconditions_topic.setTitle("pc: 前置条件")
                
                # 五级：每个前置条件
                for precondition in case['preconditions']:
                    pc_item = preconditions_topic.addSubTopic()
                    pc_item.setTitle(precondition)
            
            # 四级：操作步骤
            steps_topic = case_topic.addSubTopic()
            steps_topic.setTitle("操作步骤")
            
            # 五级：每个步骤
            for i, step in enumerate(case['steps'], 1):
                step_item = steps_topic.addSubTopic()
                step_item.setTitle(f"{i}. {step}")
                
                # 六级：预期结果（只在最后一个步骤下添加）
                if i == len(case['steps']):
                    expected_topic = step_item.addSubTopic()
                    expected_topic.setTitle(f"预期结果: {case['expected']}")
    
    # 保存文件(旧版 XMind 8 系所需的 content.xml / styles.xml)
    xmind.save(workbook, xmind_file_path)

    # 追加新版 XMind(2020 及以后,含 XMind 26)所需的 Zen 结构,
    # 并补上旧版规范要求的 META-INF/manifest.xml,使同一个包新旧版本都能打开
    def _zen_topic(title_text):
        return {"id": str(uuid.uuid4()), "title": title_text}

    def _zen_case_topic(case):
        case_topic = _zen_topic(f"tc: {case['title']}")
        children = []
        if case["preconditions"]:
            pc_topic = _zen_topic("pc: 前置条件")
            pc_topic["children"] = {"attached": [_zen_topic(p) for p in case["preconditions"]]}
            children.append(pc_topic)
        steps_topic = _zen_topic("操作步骤")
        step_topics = []
        for i, step in enumerate(case["steps"], 1):
            step_topic = _zen_topic(f"{i}. {step}")
            if i == len(case["steps"]):
                step_topic["children"] = {"attached": [_zen_topic(f"预期结果: {case['expected']}")]}
            step_topics.append(step_topic)
        steps_topic["children"] = {"attached": step_topics}
        children.append(steps_topic)
        case_topic["children"] = {"attached": children}
        return case_topic

    zen_modules = []
    for module_name, module_cases in modules.items():
        module_topic = _zen_topic(module_name)
        module_topic["children"] = {"attached": [_zen_case_topic(c) for c in module_cases]}
        zen_modules.append(module_topic)

    zen_content = [{
        "id": str(uuid.uuid4()),
        "revisionId": str(uuid.uuid4()),
        "class": "sheet",
        "rootTopic": {
            "id": str(uuid.uuid4()),
            "class": "topic",
            "title": "测试用例",
            "structureClass": "org.xmind.ui.logic.right",
            "children": {"attached": zen_modules},
        },
    }]
    zen_metadata = {
        "dataStructureVersion": "3",
        "creator": {"name": "testcase-generator", "version": "1.0"},
        "layoutEngineVersion": "5",
    }
    zen_manifest = {"file-entries": {"content.json": {}, "metadata.json": {}}}
    legacy_manifest = (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        '<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">'
        '<file-entry full-path="content.xml" media-type="text/xml"/>'
        '<file-entry full-path="styles.xml" media-type="text/xml"/>'
        '<file-entry full-path="META-INF/" media-type=""/>'
        '<file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>'
        '</manifest>'
    )

    with zipfile.ZipFile(xmind_file_path, "a", zipfile.ZIP_STORED) as archive:
        archive.writestr("content.json", json.dumps(zen_content, ensure_ascii=False))
        archive.writestr("metadata.json", json.dumps(zen_metadata, ensure_ascii=False))
        archive.writestr("manifest.json", json.dumps(zen_manifest, ensure_ascii=False))
        archive.writestr("META-INF/manifest.xml", legacy_manifest)


def main():
    # 命令参数定义
    parser = argparse.ArgumentParser(description="解析 cases.json 并写入 xmind")
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

    xmind_file_path = f"测试用例_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.xmind"
    try:
        export_xmind(cases_json_path=full_path, xmind_file_path=xmind_file_path)
        print(f"xmind 文件生成成功: {str(Path(xmind_file_path).expanduser().resolve())}")
        sys.exit(0)
    except Exception as e:
        print(f"xmind 文件生成失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()