from utils.parser import parse_llm_json

def test_conversational_noise():
    content = """
    Tentu, ini adalah hasil analisis saya:
    ```json
    {
        "status": "success",
        "confidence": 0.9
    }
    ```
    Semoga membantu!
    """
    result = parse_llm_json(content)
    assert result["status"] == "success"
    assert result["confidence"] == 0.9

def test_trailing_commas():
    content = '{"key": "value",}'
    result = parse_llm_json(content)
    assert result["key"] == "value"

def test_comments_and_smart_quotes():
    content = """
    {
        "key": "value", // Ini komentar
        "smart": “quote”
    }
    """
    result = parse_llm_json(content)
    assert result["key"] == "value"
    assert result["smart"] == "quote"

def test_multiple_blocks():
    content = """
    Block 1:
    ```json
    {"id": 1}
    ```
    Block 2 (bigger):
    ```json
    {"id": 2, "description": "larger block"}
    ```
    """
    result = parse_llm_json(content)
    # Our implementation sorts by length DESC
    assert result["id"] == 2

def test_invalid_control_chars():
    # Including a null byte or similar
    content = '{"key": "value\u0000"}'
    result = parse_llm_json(content)
    assert result["key"].startswith("value")

if __name__ == "__main__":
    try:
        test_conversational_noise()
        print("test_conversational_noise passed")
        test_trailing_commas()
        print("test_trailing_commas passed")
        test_comments_and_smart_quotes()
        print("test_comments_and_smart_quotes passed")
        test_multiple_blocks()
        print("test_multiple_blocks passed")
        test_invalid_control_chars()
        print("test_invalid_control_chars passed")
        print("\nAll robust tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        exit(1)
