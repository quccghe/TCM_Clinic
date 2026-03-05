SYNDROME_SLOTS = {
    "fever_infection": {
        "triggers": ["发热", "高热", "寒战", "畏寒", "咽痛", "咳", "黄痰", "脓痰"],
        "critical_questions": [
            "是否测量过体温？最高体温大约多少（如38.5℃）？",
            "寒战是否反复出现？退热后是否出汗？",
            "咳嗽是干咳还是有痰？痰色（白稀/黄稠/带血）如何？"
        ],
        "critical_slot_tags": ["temp_level", "chills", "sweat_after_fever", "phlegm_type"],
    },

    "cardio_respiratory": {
        "triggers": ["胸痛", "胸闷", "呼吸困难", "气促", "心悸", "咯血"],
        "critical_questions": [
            "是否出现气促或静息时呼吸费力？活动后是否明显加重？",
            "是否胸痛/胸闷？深呼吸或咳嗽时是否加重？",
            "是否咯血或口唇发紫？"
        ],
        "critical_slot_tags": ["dyspnea", "chest_pain", "hemoptysis"],
    },

    "jaundice": {
        "triggers": ["黄疸", "眼白黄", "皮肤黄", "尿黄", "茶色尿", "胁痛", "右胁痛", "厌油", "纳差"],
        "critical_questions": [
            "眼白或皮肤有没有发黄？大概从什么时候开始？",
            "小便颜色是淡黄、深黄还是像浓茶？大便颜色有没有变浅或发灰？",
            "有没有皮肤瘙痒、发热寒战、右上腹/胁肋疼痛或压痛？"
        ],
        "critical_slot_tags": ["yellowing", "urine_color", "stool_color", "itching", "ruq_pain", "fever_chills"],
    },

    "metabolic_wasting": {
        "triggers": ["口渴", "多饮", "尿多", "尿频", "易饥", "多食", "消瘦", "体重下降", "乏力"],
        "critical_questions": [
            "是否出现多饮、多尿、多食易饥或体重下降？持续多久？",
            "夜尿多吗？小便量是否明显增加？",
            "口渴喜冷还是喜温？喝水后能否缓解？"
        ],
        "critical_slot_tags": ["polydipsia", "polyuria", "polyphagia", "weight_loss", "drink_preference"],
    },
}