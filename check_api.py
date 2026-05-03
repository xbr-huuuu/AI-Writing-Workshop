"""
API连接诊断脚本 —— 测试DeepSeek API是否可用
用法：python check_api.py
"""
from openai import OpenAI

API_KEY = "sk-0caaef224d0049ccb7af362612c994e5"

print("=" * 50)
print("🔍 DeepSeek API 连接诊断")
print("=" * 50)

# 测试1：默认 base_url（不带 /v1）
print("\n[测试1] base_url = https://api.deepseek.com")
try:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
    r = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": "回复OK"}],
        max_tokens=10,
    )
    print(f"  ✓ 成功！响应：{r.choices[0].message.content}")
except Exception as e:
    print(f"  ✗ 失败：{e}")

# 测试2：带 /v1 的 base_url
print("\n[测试2] base_url = https://api.deepseek.com/v1")
try:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")
    r = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": "回复OK"}],
        max_tokens=10,
    )
    print(f"  ✓ 成功！响应：{r.choices[0].message.content}")
except Exception as e:
    print(f"  ✗ 失败：{e}")

# 测试3：尝试 deepseek-chat 模型名
print("\n[测试3] model = deepseek-chat, base_url = https://api.deepseek.com")
try:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "回复OK"}],
        max_tokens=10,
    )
    print(f"  ✓ 成功！响应：{r.choices[0].message.content}")
except Exception as e:
    print(f"  ✗ 失败：{e}")

# 测试4：尝试 deepseek-chat + /v1
print("\n[测试4] model = deepseek-chat, base_url = https://api.deepseek.com/v1")
try:
    client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "回复OK"}],
        max_tokens=10,
    )
    print(f"  ✓ 成功！响应：{r.choices[0].message.content}")
except Exception as e:
    print(f"  ✗ 失败：{e}")

print("\n" + "=" * 50)
print("诊断完成。找到成功的组合后告诉我，我来更新配置。")
