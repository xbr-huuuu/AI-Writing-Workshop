"""
LLM客户端 —— 统一封装 DeepSeek / OpenAI / Anthropic 调用
"""
import traceback
from typing import Optional
from config import config


class LLMClient:
    """统一的大模型调用接口，优先使用 DeepSeek"""

    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None

    @property
    def openai_client(self):
        """OpenAI 兼容客户端（DeepSeek / OpenAI / 中转API 均走此通道）"""
        if self._openai_client is None:
            from openai import OpenAI

            # 优先使用 DeepSeek 配置
            api_key = config.deepseek_api_key or config.openai_api_key
            base_url = config.deepseek_base_url
            if config.openai_base_url:
                base_url = config.openai_base_url  # 显式设置的 BASE_URL 优先级最高

            self._openai_client = OpenAI(api_key=api_key, base_url=base_url)
        return self._openai_client

    @property
    def anthropic_client(self):
        if self._anthropic_client is None:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        return self._anthropic_client

    def _is_claude_model(self, model: str) -> bool:
        return "claude" in model.lower()

    def chat(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> str:
        model = model or config.writer_model
        temp = temperature if temperature is not None else config.default_temperature

        try:
            if self._is_claude_model(model):
                return self._chat_anthropic(system, user, model, temp, max_tokens)
            else:
                return self._chat_openai(system, user, model, temp, max_tokens)
        except Exception:
            traceback.print_exc()
            raise

    def _chat_openai(self, system: str, user: str, model: str, temp: float, max_tokens: int) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        resp = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    def _chat_anthropic(self, system: str, user: str, model: str, temp: float, max_tokens: int) -> str:
        resp = self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temp,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text


# 全局实例
llm = LLMClient()
