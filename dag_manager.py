# dag_manager.py

import datetime
import uuid

# In-Memory-Speicher (du kannst das auch persistent machen, z. B. mit Supabase oder Datei)
dag_log = []

def generate_dag_id(step_type: str) -> str:
    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return f"{step_type}_{now}_{uuid.uuid4().hex[:6]}"

def add_dag_step(step_type: str, input_data: dict, output_data: dict, depends_on: list[str] = []) -> dict:
    dag_id = generate_dag_id(step_type)
    node = {
        "id": dag_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "type": step_type,
        "input": input_data,
        "output": output_data,
        "depends_on": depends_on
    }
    dag_log.append(node)
    return node

def get_dag() -> list[dict]:
    return dag_log

def reset_dag():
    global dag_log
    dag_log = []

def export_dag_json() -> str:
    import json
    return json.dumps(dag_log, indent=2, ensure_ascii=False)
