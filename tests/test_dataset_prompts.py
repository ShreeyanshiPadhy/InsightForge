from ai import llm


def test_dataset_ai_prompts_do_not_impose_debtor_or_currency_assumptions(monkeypatch):
    calls = []

    def capture_prompt(dataset_data, prompt):
        calls.append((dataset_data, prompt))
        return "ok"

    monkeypatch.setattr(llm, "generate_insight", capture_prompt)

    assert llm.generate_dataset_summary('{"profile": {}}') == "ok"
    assert llm.answer_dataset_question("Summarize sales.", "{}") == "ok"

    assert calls[0][0] == '{"profile": {}}'
    assert "Do not assume the dataset contains debtors" in calls[0][1]
    assert "Use Indian Rupee" not in calls[0][1]
    assert calls[1][0] == "{}"
    assert "Summarize sales." in calls[1][1]
    assert "Do not assume debtor or receivables data" in calls[1][1]
