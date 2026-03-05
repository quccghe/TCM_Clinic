import os
from typing import Optional
from master_agent import MasterAgent
from skills.case_store_skill import load_case

WELCOME = """✅ 中医问诊系统（终端模式）
- 直接输入症状开始
- 指令：
  - exit    退出
  - case    显示当前case简要信息
  - open    打印当前病例json路径
"""

def main():
    agent = MasterAgent()
    case_id: Optional[str] = None

    print(WELCOME)
    print("系统：欢迎使用。请描述你现在最主要的不舒服（持续多久、怎么开始的）。")

    while True:
        try:
            user_in = input("用户：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n系统：已退出。")
            return

        if not user_in:
            continue
        if user_in.lower() in ("exit","quit","q"):
            print("系统：已退出。")
            return

        if user_in.lower() == "case":
            if not case_id:
                print("系统：当前还没有 case_id。")
            else:
                c = load_case(case_id)
                ss = c.get("slot_status", {})
                print(f"系统：case_id={case_id} state={c.get('state')} slot_ratio={ss.get('ratio')} router={c.get('router')} decision={c.get('decision')}")
            continue

        if user_in.lower() == "open":
            if not case_id:
                print("系统：当前还没有 case_id。")
            else:
                print("系统：病例文件路径：", os.path.abspath(os.path.join("./cases", case_id + ".json")))
            continue

        res = agent.chat(user_in, case_id=case_id)
        case_id = res["case_id"]
        print("系统：" + res["message"])

if __name__ == "__main__":
    main()