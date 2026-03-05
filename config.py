import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
if cors_origins.strip() == "*":
    CORS_ALLOW_ORIGINS = ["*"]
else:
    CORS_ALLOW_ORIGINS = [x.strip() for x in cors_origins.split(",") if x.strip()]

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:9000")
RAG_VEC_DIR = os.getenv("RAG_VEC_DIR", r"G:\TCM_Clinic\pythonProject\data\rag_out_vec")

CASES_DIR = os.getenv("CASES_DIR", "./cases")
EXPORT_DIR = os.getenv("EXPORT_DIR", "./cases/exports")
RAG_SOURCE_FILE = os.getenv("RAG_SOURCE_FILE", "./data/tcm_knowledge.txt")

MAX_TURNS = int(os.getenv("MAX_TURNS", "20"))
MAX_QUESTIONS_PER_TURN = int(os.getenv("MAX_QUESTIONS_PER_TURN", "3"))
DIAG_CONF_THRESHOLD = float(os.getenv("DIAG_CONF_THRESHOLD", "0.85"))
MAX_CONSECUTIVE_DECLINES = int(os.getenv("MAX_CONSECUTIVE_DECLINES", "1"))

SLOT_DIAG_TRIGGER = float(os.getenv("SLOT_DIAG_TRIGGER", "0.70"))

RED_FLAG_KEYWORDS = [
    "胸痛", "呼吸困难", "咯血", "昏迷", "抽搐", "大出血",
    "自杀", "轻生", "严重过敏", "喉头水肿",
    "高热不退", "意识模糊", "剧烈腹痛",
    "黑便", "便血", "呕血",
]
