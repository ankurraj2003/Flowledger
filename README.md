# ⚙️ Flowledger V1.0.0
### AI-Driven Batch Invoice Scanner → Consolidated ERP Ledger

Flowledger is a premium, industrial-grade data extraction tool designed to automate the transition from digital PDF invoices to structured ERP-ready entries. Powered by the Groq LPU™ Inference Engine, it processes batch uploads with high precision, mapping line items to internal SKUs.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq_LLM-f36036?style=for-the-badge&logo=Groq&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## 🚀 Key Features

- **Batch Processing**: Upload multiple PDF invoices simultaneously and process them in a single click.
- **AI-Powered Extraction**: Utilizes Groq (LLM) to intelligently extract vendor details, invoice numbers, dates, and complex line items.
- **Smart SKU Mapping**: Automatically enriches extracted items with internal SKUs using fuzzy matching or predefined logic.
- **Visual Review & Edit**: A dedicated dashboard to validate AI output, edit item quantities/prices, and handle manual reviews.
- **Industrial Export**: Batch export to consolidated Excel formats optimized for Tally, Zoho, and other ERP systems.
- **Premium Industrial Theme**: High-contrast dark mode interface designed for readability and efficiency.

---

## 🛠️ Tech Stack

- **Core**: Python 3.12+
- **Frontend**: Streamlit (with custom CSS injection)
- **AI Engine**: Groq SDK (Llama 3/Mistral models)
- **PDF Extraction**: `pdfplumber`, `pypdfium2`
- **Data Handling**: `pandas`, `openpyxl`
- **Environment**: `python-dotenv`

---

## 📦 System Setup

### 1. Prerequisites
- Python 3.10 or higher installed.
- A Groq API Key (Get one at [console.groq.com](https://console.groq.com/)).

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/ankurraj2003/Flowledger.git
cd Flowledger
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the App
Launch the Streamlit server:
```bash
streamlit run app.py
```
The app will be available at `http://localhost:8501`.

---

## 🔄 Workflow

1. **Upload**: Drag and drop your digital PDF invoices into the **Upload** tab.
2. **Process**: Click `⚡ PROCESS ALL INVOICES`. The system extracts text, sends it to the AI for analysis, and maps SKUs.
3. **Review**: Switch to the **Review & Edit** tab to verify totals, adjust quantities, or fix mapping errors.
4. **Export**: Go to the **Export & Sync** tab to download your consolidated ledger or generate ERP-specific files.

---

## 🛡️ Security & Privacy
- **Local Context**: Invoices are processed in memory; no data is permanently stored on disk unless exported by the user.
- **API Security**: Your Groq API key is managed locally via environment variables.

---
*Built with ❤️ for industrial automation.*
