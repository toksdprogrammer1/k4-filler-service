from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
import tempfile
import os
from typing import Optional
import json
from .k4_document_processor import K4DocumentProcessor, K4FormFiller
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-statement")
async def process_statement(
    file: UploadFile = File(...),
    tax_year: str = Form(...),
    broker_name: str = Form(...),
    account_number: str = Form(...),
    taxpayer_name: str = Form(...),
    taxpayer_sin: str = Form(...)
):
    try:
        print(f"Processing statement with tax_year={tax_year}")
        
        # Create temporary files for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_statement:
            try:
                content = await file.read()
                temp_statement.write(content)
                temp_statement.flush()
                
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'k4_template.pdf')
                if not os.path.exists(template_path):
                    raise HTTPException(
                        status_code=500,
                        detail=f"Template file not found at {template_path}"
                    )
                
                claude_api_key = os.getenv("ANTHROPIC_API_KEY")
                if not claude_api_key:
                    raise HTTPException(
                        status_code=500,
                        detail="ANTHROPIC_API_KEY not configured on server"
                    )

                # Create form data dictionary
                form_data = {
                    "tax_year": tax_year,
                    "broker_name": broker_name,
                    "account_number": account_number,
                    "taxpayer_name": taxpayer_name,
                    "taxpayer_sin": taxpayer_sin
                }

                print("Processing document...")
                # Pass form_data to process_and_fill_k4
                filled_form = process_and_fill_k4(
                    statement_path=temp_statement.name,
                    k4_template_path=template_path,
                    claude_api_key=claude_api_key,
                    form_data=form_data  # Add this parameter
                )

                pdf_bytes = filled_form.getvalue()
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

                return {
                    "status": "success",
                    "message": "K4 form processed successfully",
                    "pdf_content": pdf_base64
                }

            except Exception as e:
                print(f"Error processing document: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            
            finally:
                try:
                    os.unlink(temp_statement.name)
                except Exception as e:
                    print(f"Error cleaning up temporary file: {str(e)}")

    except Exception as e:
        print(f"Outer error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def process_and_fill_k4(statement_path: str, k4_template_path: str, claude_api_key: str, form_data: dict):
    """Process statement and fill K4 form"""
    doc_processor = K4DocumentProcessor(claude_api_key)
    form_filler = K4FormFiller(k4_template_path)

    try:
        # Process activity statement
        analysis_data = doc_processor.analyze_documents(statement_path)
        
        # Add form data to analysis data
        analysis_data.update(form_data)
        
        # Fill K4 form with combined data
        filled_form = form_filler.fill_form(analysis_data)
        
        return filled_form

    except Exception as e:
        raise Exception(f"Error processing documents: {str(e)}")

# Add this at the end of the file
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,  # 5 minutes
        timeout_notify=300,
        timeout_graceful_shutdown=300,
    ) 