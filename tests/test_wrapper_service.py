# test_wrapper_service.py
import json
import requests

URL = "http://127.0.0.1:18080/minecontext_summary"

if __name__ == "__main__":
    print("Testing MineContext Wrapper Service...")
    print(f"URL: {URL}")
    try:
        resp = requests.post(URL, json={
            "task_type": "debug_error",
            "detail_level": "medium"
        }, timeout=5)
        print("Status code:", resp.status_code)
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("\n✓ Test completed successfully!")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to the service.")
        print("Make sure you started the service first with: python wrapper_service.py")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
