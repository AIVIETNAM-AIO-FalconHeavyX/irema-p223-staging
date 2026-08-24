from src.agents.state import AgentState


async def entity_extractor_node(state: AgentState) -> dict:
    """Trích xuất dòng xe máy điện từ câu hỏi người dùng."""
    query = state.get("query") or state.get("raw_query") or ""
    query_lower = query.lower()

    # Mapping tên hiển thị → vehicle_model chuẩn
    vehicle_models = {
        "evo grand lite": "Evo Grand Lite",
        "evo grand": "Evo Grand",
        "evo lite": "Evo Lite",
        "evo": "Evo",
        "flazz max": "Flazz Max",
        "flazz": "Flazz",
        "feliz 2025": "Feliz 2025",
        "feliz ii": "Feliz II",
        "viper": "Viper",
        "amio s2": "Amio S2",
        "amio s": "Amio S",
        "amio": "Amio",
        "zgoo": "Zgoo",
        "verox": "VeroX",
        "kyo": "Kyo",
        "kinet": "Kinet",
    }

    vehicle_model = "unknown"

    # Kiểm tra tên dài trước để tránh match nhầm tên ngắn
    # Ví dụ: "Evo Grand Lite" không bị match thành "Evo"
    for model_name in sorted(vehicle_models, key=len, reverse=True):
        if model_name in query_lower:
            vehicle_model = vehicle_models[model_name]
            break

    return {
        "raw_query": query,
        "vehicle_model": vehicle_model,
    }
