import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.graph import agent


async def test_chat():
    print("=== TEST END-TO-END CHATBOT VỚI DỮ LIỆU ===", flush=True)
    query = "Quy trình bán hàng xe máy điện gồm những bước nào?"
    print(f"Câu hỏi: {query}", flush=True)
    print("User Role: sales", flush=True)

    result = await agent.ainvoke(
        {
            "query": query,
            "raw_query": query,
            "user_role": "sales",
        }
    )

    print("\n--- KẾT QUẢ TỪ CHATBOT ---", flush=True)
    print(f"Intent nhận diện: {result.get('intent')}", flush=True)
    print(f"Trích dẫn nguồn (Citations): {result.get('citations')}", flush=True)
    print(f"Câu trả lời:\n{result.get('response')}", flush=True)


if __name__ == "__main__":
    asyncio.run(test_chat())
