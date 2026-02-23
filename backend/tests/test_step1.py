"""Step 1 Tests: DB CRUD, S3, BaseAgent conversation, Tool loop."""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()


def test_db_crud():
    """Test DB tables exist and CRUD works."""
    print("=== Test: DB CRUD ===")
    from core.database import get_session_factory, User, Session as DBSession

    SessionFactory = get_session_factory()
    db = SessionFactory()

    try:
        # Create user
        user = User(settings={"language": "en"})
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"  Created user: {user.id}")

        # Create session
        session = DBSession(
            user_id=user.id,
            company="Databricks",
            role="Solutions Engineer",
            mode="practice",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"  Created session: {session.id}")

        # Read
        fetched = db.query(DBSession).filter_by(id=session.id).first()
        assert fetched is not None
        assert fetched.company == "Databricks"
        print(f"  Read session: company={fetched.company}, role={fetched.role}")

        # Update
        fetched.status = "interviewing"
        db.commit()
        db.refresh(fetched)
        assert fetched.status == "interviewing"
        print(f"  Updated status: {fetched.status}")

        # Delete
        db.delete(fetched)
        db.delete(user)
        db.commit()
        print("  Deleted user and session")

        print("[PASS] DB CRUD")
    finally:
        db.close()


def test_s3_upload_download():
    """Test S3 upload and download helper."""
    print("\n=== Test: S3 Upload/Download ===")
    from core.s3_client import upload_file, download_file, delete_file

    test_content = b"Test resume PDF content"
    session_id = str(uuid.uuid4())

    # Upload
    s3_key = upload_file(test_content, "resume.pdf", "resume", session_id)
    print(f"  Uploaded to: {s3_key}")

    # Download
    downloaded = download_file(s3_key)
    assert downloaded == test_content
    print("  Downloaded and verified content match")

    # Cleanup
    delete_file(s3_key)
    print("  Cleaned up")

    print("[PASS] S3 Upload/Download")


def test_agent_conversation():
    """Test BaseAgent can converse with Claude via Bedrock."""
    print("\n=== Test: BaseAgent Conversation ===")
    from agents.base_agent import BaseAgent
    from tools.registry import ToolRegistry

    registry = ToolRegistry()
    agent = BaseAgent(registry=registry, model="haiku")
    agent.system_prompt = "You are a helpful assistant. Be very brief."

    response = agent.run("What is 2 + 2? Answer with just the number.")
    print(f"  Agent response: {response.strip()}")
    assert "4" in response
    print("[PASS] BaseAgent Conversation")


def test_tool_loop():
    """Test: LLM receives tools -> tool_use -> execute -> return result -> continue."""
    print("\n=== Test: Tool Use Loop ===")
    from agents.base_agent import BaseAgent
    from tools.registry import ToolRegistry

    registry = ToolRegistry()

    # Register a simple test tool
    def get_weather(city: str) -> dict:
        return {"city": city, "temperature": "22C", "condition": "sunny"}

    registry.register(
        name="get_weather",
        description="Get the current weather for a city.",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"],
        },
        handler=get_weather,
    )

    agent = BaseAgent(registry=registry, model="haiku", tool_names=["get_weather"])
    agent.system_prompt = (
        "You have a get_weather tool. When asked about weather, "
        "use the tool first, then respond with the result. Be brief."
    )

    response = agent.run("What is the weather in Seoul?")
    print(f"  Agent response: {response.strip()}")
    assert "22" in response or "sunny" in response.lower() or "seoul" in response.lower()

    # Verify tool was actually called (check memory for tool_result)
    tool_used = any(
        isinstance(msg.get("content"), list)
        and any(
            item.get("type") == "tool_result"
            for item in msg["content"]
            if isinstance(item, dict)
        )
        for msg in agent.memory
    )
    assert tool_used, "Tool was not called!"
    print("  Tool was called and result returned to LLM")
    print("[PASS] Tool Use Loop")


if __name__ == "__main__":
    tests = [test_db_crud, test_s3_upload_download, test_agent_conversation, test_tool_loop]
    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Step 1 tests PASSED!")
