import os
import re
from dotenv import load_dotenv
from openai import AzureOpenAI
from database import execute_query
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME=os.getenv("DEPLOYMENT_NAME")
OPENAI_API_VERSION=os.getenv("API_VERSION")


AZURE_SEARCH_ENDPOINT=os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY=os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME=os.getenv("INDEX_NAME")
TEXT_EMBEDDING_MODEL=os.getenv("TEXT_EMBEDDING_MODEL")
SEARCH_API_VERSION=os.getenv("SEARCH_API_VERSION")

#Azure search Setup
search_client=SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

def search_index(query_text, document_type, top=5):
    """Retrieve table or relationship metadata, never a mixed result set."""
    return list(
        search_client.search(
            search_text=query_text,
            filter=f"type eq '{document_type}'",
            top=top,
        )
    )

def build_schema_context(table_docs, relationship_docs):
    """Clearly separate usable SQL tables from join-description documents."""
    tables = "\n\n".join(
        (
            f"Table: {doc.get('name', '')}\n"
            f"Description: {doc.get('description', '')}\n"
            f"Columns: {doc.get('columns', '')}"
        )
        for doc in table_docs
    )
    relationships = "\n".join(
        f"- {doc.get('name', '')}: {doc.get('description', '')}"
        for doc in relationship_docs
    )
    return f"SQL TABLES:\n{tables}\n\nJOIN RELATIONSHIPS:\n{relationships}"


def invalid_table_names(sql, table_docs):
    """Return names after FROM/JOIN that are not real table names."""
    allowed_tables = {doc.get("name", "").lower() for doc in table_docs}
    referenced_tables = re.findall(r"\b(?:FROM|JOIN)\s+([^\s;]+)", sql, re.IGNORECASE)
    return [
        table.strip("`").lower()
        for table in referenced_tables
        if table.strip("`").lower() not in allowed_tables
    ]


def is_safe_select(sql):
    """Allow exactly one SELECT statement before sending SQL to MySQL."""
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
    return len(statements) == 1 and statements[0].lower().startswith("select")


client=AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION
)
def clean_sql(sql:str):
    lines=sql.strip().splitlines()
    cleaned_lines=[line for line in lines if not line.strip().startswith("```")]
    return "\n".join(cleaned_lines)


def generate_sql(messages):
    """Call the model and remove Markdown code fences from its response."""
    response=client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        temperature=0,
        max_tokens=150
    )
    return clean_sql(response.choices[0].message.content.strip())

def question_to_sql(question: str, previous_sql=None, database_error=None):

    # Tables may be used in SQL; relationships only explain JOIN keys.
    table_docs = search_index(question, document_type="table", top=5)
    relationship_docs = search_index(question, document_type="relationship", top=5)
    context = build_schema_context(table_docs, relationship_docs)


    system_prompt = f"""
You convert natural-language business questions into MySQL queries.

Use this database schema:
{context}

Rules:
- Use only table and column names explicitly present in the schema above.
- Never invent column names.
- Add necessary JOINs using the available *_id columns.
- Only names under “SQL TABLES” may appear after FROM or JOIN.
- Names under “JOIN RELATIONSHIPS” are descriptions only; never use them as SQL table names.
- Use relationship information only to determine JOIN conditions.
- Before returning SQL, verify every table and column exists in the supplied schema.
- Return exactly one read-only SELECT query and no explanation.
- If the question has more than one valid meaning, do not guess. Return:
  CLARIFY: <a short question that lets the user choose>
"""
    message= [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    # When MySQL rejects a query (for example, for an unknown column), give
    # the model the exact error and one opportunity to create a corrected query.
    if previous_sql and database_error:
        message.extend([
            {"role": "assistant", "content": previous_sql},
            {"role": "user", "content": (
                f"The previous SQL failed with this MySQL error: {database_error}. "
                "Correct it using only the supplied schema."
            )},
        ])

    clean_sql_query = generate_sql(message)

    # The prompt asks for SELECT only; this guard enforces it in code.
    if not clean_sql_query.startswith("CLARIFY:") and not is_safe_select(clean_sql_query):
        return "INVALID_SQL: Only one read-only SELECT statement is allowed."

    # Reject a relationship label used as a table name and request one repair.
    invalid_tables = invalid_table_names(clean_sql_query, table_docs)
    if invalid_tables and not clean_sql_query.startswith("CLARIFY:"):
        message.extend([
            {"role": "assistant", "content": clean_sql_query},
            {"role": "user", "content": (
                f"The SQL used invalid table name(s): {', '.join(invalid_tables)}. "
                "Regenerate it using only names listed under SQL TABLES."
            )},
        ])
        clean_sql_query = generate_sql(message)
        if not is_safe_select(clean_sql_query):
            return "INVALID_SQL: Only one read-only SELECT statement is allowed."
        invalid_tables = invalid_table_names(clean_sql_query, table_docs)

    # Do not pass an uncorrected invalid query to MySQL.
    if invalid_tables:
        return f"INVALID_SQL: Unknown table name(s): {', '.join(invalid_tables)}"

    return clean_sql_query

def get_sql_with_clarification(question, max_attempts=2):

    for _ in range(max_attempts):
        response = question_to_sql(question)

        if not response.startswith("CLARIFY:"):
            return response
        clarification = response.removeprefix("CLARIFY:").strip()
        answer=input(f"\n{clarification}\nYour answer:").strip()

        if not answer:
            return "INVALID_SQL: No clarification answer was provided."
        # Preserve both the original request and the user's clarification.

        question = f"""
Original user question:
{question}

Clarification answer from user:
{answer}

Generate the SQL query now.
"""

    return "INVALID_SQL: The question remained ambiguous after clarification."


if __name__=="__main__":
    question = """
Show the top 3 customer-product combinations by total quantity ordered.
Return customer_id, company_name, product_name, and total quantity.
"""
    sql_query=get_sql_with_clarification(question)
    print("Generated SQL:\n", sql_query)

    # Model status responses are application text, never executable SQL.
    if sql_query.startswith(("CLARIFY:", "INVALID_SQL:")):
        print("\nApplication response:\n", sql_query)
        raise SystemExit(0)

    # Execute the generated query using the database connection
    try:
        query_results=execute_query(sql_query)
        print("Query results:\n", query_results)
    except Exception as e:
        print("Initial query failed:", e)

        # A database error can reveal an invented column or an invalid JOIN.
        # Retry once with the error details; a second failure is reported only.
        corrected_sql = question_to_sql(
            question,
            previous_sql=sql_query,
            database_error=str(e),
        )
        print("Corrected SQL:\n", corrected_sql)

        if corrected_sql.startswith(("CLARIFY:", "INVALID_SQL:")):
            print("\nApplication response:\n", corrected_sql)
            raise SystemExit(0)

        try:
            query_results=execute_query(corrected_sql)
            print("Query results after correction:\n", query_results)
        except Exception as correction_error:
            print("Corrected query also failed:", correction_error)
