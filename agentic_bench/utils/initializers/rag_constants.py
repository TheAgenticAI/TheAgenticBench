from pathlib import Path

PDF_DIRECTORY = Path(__file__).resolve().parents[2] / 'Pdf_data_folder'
WORKING_DIR = Path(__file__).resolve().parents[2] / 'graph_data_folder'

rag_system_prompt = """You are a helpful AI assistant that processes queries using RAG (Retrieval Augmented Generation).
 Use the provided RAG system to retrieve relevant information and generate comprehensive responses.
 Always aim to provide accurate and contextual information based on the retrieved content. 
 If you don't know the answer, just say that you don't know and return a bool of False.
 Also, tell the user that these entities were used to generate the response.
 Use the provided tools to retrieve information and answer the user's question.
 MAKE SURE YOU CALL THE PROVIDED TOOLS ATLEAST ONCE TO GET THE ANSWER.

 """
rag_description = " An AI assistant specialized in answering from users using the data uploaded by user"

DOMAIN = (
    "Analyze and interpret financial reports, including 10-K and 10-Q filings, "
    "to provide actionable insights into the company's financial performance, "
    "cash flows, risks, strategies, and operational efficiency. The analysis "
    "should focus on key financial metrics such as net cash flow, revenue, "
    "expenses, liabilities, and assets, as well as qualitative factors like "
    "strategies for growth, risk mitigation approaches, and overall financial health. "
    "In addition, extract data trends, compare performance across periods, and "
    "identify anomalies or significant changes."
)

EXAMPLE_QUERIES = [
    "What is the net cash from operating activities in the Q3 2022 report?",
    "What are the key risks highlighted in the latest 10-K filing?",
    "What strategies did the company implement for revenue growth?",
    "What are the significant changes in expenses compared to the previous quarter?",
    "What are the projected cash flows for the next quarter?",
    "What was the year-over-year growth in revenue based on the 2021 and 2022 reports?",
    "What are the company's largest operating expenses, and how have they changed over time?",
    "Which risks related to market conditions were discussed in the latest 10-Q filing?",
    "What is the company's current debt-to-equity ratio as stated in the financial reports?",
    "How does the company's net income trend over the last four quarters?",
    "What are the major drivers of cash flow from investing activities?",
    "Which new strategies for cost reduction were outlined in the latest 10-K?",
    "How does the company plan to address risks associated with supply chain disruptions?",
    "What are the main contributors to changes in net working capital compared to the previous year?",
    "Has the company made any major acquisitions, and what financial impact did they report?",
    "What are the primary factors affecting gross margin in recent reports?",
    "What operational efficiencies were highlighted as key achievements in the latest filings?",
    "what is the value of common share price in Q3?"
]

ENTITY_TYPES = [
    "Revenue",
    "Expense",
    "Cash Flow",
    "Net Income",
    "Profit Margin",
    "Risk",
    "Strategy",
    "Asset",
    "Liability",
    "Equity",
    "Debt",
    "Investments",
    "Operating Expenses",
    "Capital Expenditures",
    "Net Working Capital",
    "Acquisitions",
    "Market Trends",
    "Supply Chain",
    "Cost Reduction",
    "Growth Strategy",
    "Tax Implications",
    "Regulatory Compliance",
    "Operational Efficiency",
    "Financial Ratios"
]

SYSTEM_PROMPT = """You are a helpful AI assistant that processes queries using RAG (Retrieval Augmented Generation).
Use the provided RAG system to retrieve relevant information and generate comprehensive responses.
Always aim to provide accurate and contextual information based on the retrieved content. 
If you don't know the answer, just say that you don't know and return a bool of False.
Also, tell the user that these entities were used to generate the response.
"""

AGENT_DESCRIPTION_FINANCE = """ RAG agent for extracting precise numerical data from corporate financial statements and reports using access to verified corporate financial records and reports in its knowledge base. """

AGENT_DESCRIPTION_RESEARCH_PAPERS = """  RAG Agent for answering questions related to academics, research papers, and technical publications in AI, ML, and NLP domains to deliver scholarly insights. """