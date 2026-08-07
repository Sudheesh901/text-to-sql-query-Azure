import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from database import execute_query
load_dotenv()

AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME=os.getenv("DEPLOYMENT_NAME")
OPENAI_API_VERSION=os.getenv("API_VERSION")

client=AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION
)
def clean_sql(sql:str):
    lines=sql.strip().splitlines()
    cleaned_lines=[line for line in lines if not line.strip().startswith("```")]
    return "\n".join(cleaned_lines)

def question_to_sql(question:str):

    system_prompt= " You are an assistant that converts natural language business questions into SQL Queries"
    message= [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    response=client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=message,
        temperature=0,
        max_tokens=150
    )

    sql=response.choices[0].message.content.strip()
    sql_query=clean_sql(sql)

    return sql_query

if __name__=="__main__":
    question="Which customers are located in Germany?"
    sql_query=question_to_sql(question)
    print(sql_query)
    query_results=execute_query(sql_query)
    print(query_results)