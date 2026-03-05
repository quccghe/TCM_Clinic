from enum import Enum

class VisitStage(str, Enum):
    INITIAL = "initial"   # 初诊
    REVISIT = "revisit"   # 复诊

# 四诊关键字段（你可以继续扩充）
FOUR_DIAG_FIELDS = [
    "chief_complaint",
    "present_illness",
    "symptoms",
    "cold_heat",
    "sweat",
    "thirst",
    "appetite",
    "stool",
    "urine",
    "sleep",
    "pain",
    "tongue",
    "pulse",
    "menses_pregnancy",
    "past_history",
    "allergy",
]

RISK_LEVELS = ["none", "low", "medium", "high"]