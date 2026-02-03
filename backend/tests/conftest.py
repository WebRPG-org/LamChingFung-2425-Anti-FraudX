"""
Test Configuration and Fixtures
Shared fixtures and configuration for all tests
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing"""
    return [
        {
            "speaker": "騙徒",
            "dialogue": "你好，我係XX銀行嘅客戶經理",
            "timestamp": "2026-02-03T10:00:00"
        },
        {
            "speaker": "受騙者",
            "dialogue": "係咪真㗎？",
            "timestamp": "2026-02-03T10:00:05"
        },
        {
            "speaker": "專家",
            "dialogue": "唔好信，立即掛線",
            "timestamp": "2026-02-03T10:00:10"
        },
        {
            "speaker": "受騙者",
            "dialogue": "好的，多謝",
            "timestamp": "2026-02-03T10:00:15"
        }
    ]


@pytest.fixture
def sample_scammer_dialogue():
    """Sample scammer dialogue for testing"""
    return {
        "authority": "你好，我係XX銀行嘅客戶經理。你嘅戶口有可疑交易。",
        "urgency": "你要立即處理，否則戶口會被凍結。",
        "benefits": "你有政府補貼可以領取，金額為$5000。",
        "combined": "我係警察，你要立即處理，否則會被捕。你有補貼可以領取。"
    }


@pytest.fixture
def sample_expert_dialogue():
    """Sample expert dialogue for testing"""
    return {
        "empathy": "唔好驚，我明白你嘅擔心。",
        "evidence": "銀行唔會咁樣聯絡你，呢個係騙案手法。",
        "actionable": "立即掛線，然後打去銀行官方熱線核實。",
        "combined": "唔好驚，我明白你嘅擔心。銀行唔會咁樣聯絡你。立即掛線。"
    }


@pytest.fixture
def sample_victim_responses():
    """Sample victim responses for testing"""
    return {
        "elderly_fear": "我好驚啊，點算好？係咪真㗎？",
        "elderly_trust": "好啊，你幫我處理啦。",
        "overconfident_challenge": "你憑咩咁講？你係咪搞錯咗？",
        "overconfident_suspicious": "呢啲我識啦，你估我傻㗎？",
        "average_hesitant": "咁...係咪真㗎？我需要時間考慮下。",
        "average_accepting": "聽落都幾合理，可唔可以講多啲？"
    }


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        "model": "gemma3:4b",
        "created_at": "2026-02-03T10:00:00Z",
        "response": "你好，我係銀行職員。",
        "done": True,
        "context": [],
        "total_duration": 1000000000,
        "load_duration": 100000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000000,
        "eval_count": 20,
        "eval_duration": 700000000
    }


@pytest.fixture
def mock_rag_results():
    """Mock RAG query results"""
    return {
        "documents": [[
            "案例1：假冒銀行職員詐騙，受害者損失$50,000",
            "案例2：假冒警察詐騙，受害者損失$100,000",
            "案例3：投資詐騙，受害者損失$200,000"
        ]],
        "metadatas": [[
            {"title": "假冒銀行職員", "date": "2025-12-01", "link": "https://example.com/1"},
            {"title": "假冒警察", "date": "2025-12-15", "link": "https://example.com/2"},
            {"title": "投資詐騙", "date": "2026-01-01", "link": "https://example.com/3"}
        ]],
        "distances": [[0.1, 0.2, 0.3]]
    }


@pytest.fixture
def temp_database(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    from config import Config
    return Config()


# Async fixtures for async tests
@pytest.fixture
async def async_client():
    """Async HTTP client for API testing"""
    import httpx
    async with httpx.AsyncClient() as client:
        yield client


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (may take >1 second)"
    )
    config.addinivalue_line(
        "markers", "asyncio: Async tests"
    )
