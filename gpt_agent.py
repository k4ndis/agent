from agent_router import get_prompt
import openai

def call_gpt_agent(user_input: str, agent_type: str, api_key: str, model: str = "gpt-4") -> str:
    prompt = get_prompt(agent_type)
    full_prompt = f"{prompt.strip()}\n\n{user_input.strip()}"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Fehler beim GPT-Antwortversuch: {e}"
