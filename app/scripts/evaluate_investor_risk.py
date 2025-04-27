from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize Local LLM
llm = Ollama(model="llama3.1")  

# Enhanced Prompt
investor_risk_prompt = PromptTemplate(
    input_variables=["answer"],
    template="""
You are acting as a Senior Investment Risk Analyst.

Your task:
- Analyze the provided due diligence answer critically.
- Consider governance, cybersecurity, legal compliance, financial transparency, operational resilience, risk management, and ESG.

Strictly classify the investor risk into exactly ONE word:

- Positive → strong compliance, strong protection, no red flags, risks are well-mitigated.
- Negative → major non-compliance, open risks without mitigation, missing audits, vulnerabilities.
- Partial → answer is vague, incomplete, or doesn't fully resolve key risks.
- Missing → question is unanswered or context is irrelevant.

When evaluating:
- If there are clear mitigations → classify as Positive.
- If there are material open risks → classify as Negative.
- If only partial coverage → classify as Partial.
- If no answer or no clear link to question → classify as Missing.

When in doubt, err conservatively.
RETURN ONLY ONE WORD. NOTHING ELSE.
Answer:
---
{answer}
---
ONLY output Positive, Negative, Partial, or Missing (without quotes).
"""
)

# Chain Setup
investor_risk_chain = LLMChain(llm=llm, prompt=investor_risk_prompt)

# Evaluation Function
def evaluate_investor_risk(answer: str) -> str:
    """Evaluate the answer professionally: Positive, Negative, Partial, Missing."""
    result = investor_risk_chain.run(answer=answer)
    return result.strip()
