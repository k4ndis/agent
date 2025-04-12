def get_prompt(agent_type: str) -> str:
    if agent_type == "analyse":
        from analyse_prompt import analyse_prompt
        return analyse_prompt
    elif agent_type == "optimierung":
        from optimierungs_prompt import optimierungs_prompt
        return optimierungs_prompt
    elif agent_type == "security":
        from security_prompt import security_prompt
        return security_prompt
    elif agent_type == "compliance":
        from compliance_prompt import compliance_prompt
        return compliance_prompt
    else:
        return "Du bist ein allgemeiner KI-Assistent. Bitte analysiere den Input sachlich und hilfreich."
