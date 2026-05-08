from utils.parser import parse_llm_json

def test_parse_valid_json():
    content = '```json\n{"key": "value"}\n```'
    result = parse_llm_json(content)
    assert result == {"key": "value"}
    print("test_parse_valid_json passed")

def test_parse_raw_json():
    content = '{"key": "value"}'
    result = parse_llm_json(content)
    assert result == {"key": "value"}
    print("test_parse_raw_json passed")

def test_parse_with_text():
    content = 'Here is the result: ```json\n{"findings": ["vulnerability"]}\n```'
    result = parse_llm_json(content)
    assert result == {"findings": ["vulnerability"]}
    print("test_parse_with_text passed")

def test_parse_error_reporting():
    content = "Invalid JSON content"
    try:
        parse_llm_json(content)
    except ValueError as e:
        assert f"({len(content)} chars)" in str(e)
        assert content in str(e)
        print(f"test_parse_error_reporting passed: {e}")

if __name__ == "__main__":
    test_parse_valid_json()
    test_parse_raw_json()
    test_parse_with_text()
    test_parse_error_reporting()
    print("All tests passed!")
