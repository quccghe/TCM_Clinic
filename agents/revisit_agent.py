from typing import Dict, Any

class RevisitAgent:
    def run(self, last_case: Dict[str, Any]) -> Dict[str, Any]:
        fd = last_case.get("four_diagnosis", {}).get("inquiry", {})
        chief = fd.get("chief_complaint", "") or "上次的主要问题"
        msg = (
            f"我们来复诊一下：围绕「{chief}」\n"
            "1) 相比上次现在是好转、加重还是波动？\n"
            "2) 这段时间作息饮食、情绪压力、运动有没有变化？\n"
            "3) 如果你做了任何干预（食疗/用药/理疗），效果如何？\n"
            "4) 舌象/睡眠/二便有没有明显变化？"
        )
        return {"message": msg}