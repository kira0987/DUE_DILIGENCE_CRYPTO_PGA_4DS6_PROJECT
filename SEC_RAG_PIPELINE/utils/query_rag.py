# utils/query_rag.py
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import matplotlib.pyplot as plt
import os

def get_llm():
    return Ollama(
        model="mistral:7b-instruct-q4_0",
        temperature=0,
        timeout=300,
        base_url='http://localhost:11434',
        num_gpu=0  # Disable GPU, force CPU
    )

def ask_question(db, question):
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert SEC filing analyst. Answer the question based only on the following context:
    <context>
    {context}
    </context>
    
    Question: {input}
    """)
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = db.as_retriever()
    chain = create_retrieval_chain(retriever, document_chain)
    
    return chain.invoke({"input": question})["answer"]

def analyze_filing_time_series(cik, company_name):
    df = pd.read_csv("sec_edgar_daily_indexes_2014_2025.csv")
    df['Date Filed'] = pd.to_datetime(df['Date Filed'], errors='coerce')
    df = df[df['CIK'] == int(cik)]

    form_counts = df['Form Type'].value_counts().to_dict()
    amended_forms = [f for f in df['Form Type'] if "/A" in str(f)]
    filing_counts = df.groupby(df['Date Filed'].dt.to_period("M")).size()

    chart_path = os.path.join("output", f"{cik}_filing_timeseries.png")
    filing_counts.plot(kind='bar', figsize=(12, 5), title=f"Filings Over Time for {company_name}")
    plt.xlabel("Month")
    plt.ylabel("Number of Filings")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    summary = f"{company_name} (CIK: {cik}) had {len(df)} filings.\n"
    summary += f"Form types found: {list(form_counts.keys())[:5]}...\n"
    summary += f"Total amended filings (/A): {len(amended_forms)}\n"

    return summary, chart_path