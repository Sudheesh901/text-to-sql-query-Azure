from fastapi.encoders import jsonable_encoder

from database import execute_query
from text_to_sql import question_to_sql


def run_question(question: str) -> dict:
    """Generate safe SQL, execute it, and return a JSON-ready response."""

    sql_query = question_to_sql(question)

    if sql_query.startswith("CLARIFY:"):
        return {
            "status": "clarification",
            "message": sql_query.removeprefix("CLARIFY:").strip(),
            "sql": None,
            "columns": [],
            "rows": [],
        }

    if sql_query.startswith("INVALID_SQL:"):
        return {
            "status": "error",
            "message": sql_query.removeprefix("INVALID_SQL:").strip(),
            "sql": None,
            "columns": [],
            "rows": [],
        }

    try:
        results = execute_query(sql_query)
    except Exception as error:
        # Reuse your existing correction behavior once.
        corrected_sql = question_to_sql(
            question,
            previous_sql=sql_query,
            database_error=str(error),
        )

        if corrected_sql.startswith("CLARIFY:"):
            return {
                "status": "clarification",
                "message": corrected_sql.removeprefix("CLARIFY:").strip(),
                "sql": None,
                "columns": [],
                "rows": [],
            }

        if corrected_sql.startswith("INVALID_SQL:"):
            return {
                "status": "error",
                "message": corrected_sql.removeprefix("INVALID_SQL:").strip(),
                "sql": None,
                "columns": [],
                "rows": [],
            }

        try:
            sql_query = corrected_sql
            results = execute_query(sql_query)
        except Exception:
            # Do not return raw database errors to public API users.
            return {
                "status": "error",
                "message": "The query could not be completed. Please rephrase your question.",
                "sql": None,
                "columns": [],
                "rows": [],
            }

    return {
        "status": "success",
        "message": None,
        "sql": sql_query,
        "columns": list(results.columns),
        "rows": jsonable_encoder(results.to_dict(orient="records")),
    }