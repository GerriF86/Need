# Vacalyser – AI-Powered Vacancy Creation Wizard

Vacalyser helps recruiters generate complete, well-structured job
specifications via a Streamlit interface backed by OpenAI’s **Agents SDK**.

## ✨  Features
* One-page progressive wizard with dynamic sections  
* Automatic field extraction from URLs or uploaded job-ad files  
* Multi-step reasoning powered by GPT-4 + tool calling  
* Strictly typed **Pydantic** models & JSON output  
* FAISS vector store for future RAG extensions  
* Built-in tracing, guardrails and validation

## 🚀  Quick start
```bash
git clone https://github.com/your-org/vacalyser.git
cd vacalyser
python -m venv .venv && source .venv/bin/activate       # or conda/mamba
pip install -r requirements.txt

# add your OpenAI key
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
$EDITOR .streamlit/secrets.toml

streamlit run app.py
