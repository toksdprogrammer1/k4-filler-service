from decimal import Decimal
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage
from PyPDF2 import PdfReader, PdfWriter
import io
from typing import Dict, List
import os
import re
from datetime import datetime

class K4DocumentProcessor:
    def __init__(self, claude_api_key: str):
        os.environ["ANTHROPIC_API_KEY"] = claude_api_key  # Set the API key in environment
        self.llm = ChatAnthropic(
            model_name="claude-3-sonnet-20240229",  # Changed from model to model_name
            temperature=0
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )

    def _load_pdf(self, pdf_path: str) -> List[str]:
        """Load and split PDF into chunks"""
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            texts = []
            for page in pages:
                text_chunks = self.text_splitter.split_text(page.page_content)
                texts.extend(text_chunks)
            return texts
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            raise

    def _create_analysis_prompt(self, statement_text: str) -> str:
        """Create prompt for analyzing trading activity with specific format instructions"""
        return f"""Analyze the following Interactive Brokers activity statement and extract information for Skatteverket K4 form tax reporting.
        Focus on futures trades in section D (Övriga värdepapper).

        Please format your response exactly as follows for each trade:
        TRADE_START
        Symbol: [instrument symbol]
        Description: [instrument description]
        Quantity: [number of contracts]
        SalePriceSEK: [total sale price in SEK]
        PurchasePriceSEK: [total purchase price in SEK]
        GainLossSEK: [gain/loss amount in SEK]
        TRADE_END

        Activity Statement:
        {statement_text}

        Provide exact numbers without formatting (no thousands separators). Use negative numbers for losses."""

    def analyze_documents(self, statement_path: str) -> Dict:
        """Process activity statement and extract K4 relevant data"""
        try:
            # Load and process statement
            statement_chunks = self._load_pdf(statement_path)

            # Create and send prompts chunk by chunk
            results = []
            for chunk in statement_chunks:
                prompt = self._create_analysis_prompt(chunk)
                response = self.llm.invoke([HumanMessage(content=prompt)])
                results.append(response.content)

            # Parse and combine results
            parsed_data = self._parse_results(results)

            # Print parsed data for debugging
            print("Parsed Data:")
            print("Instruments:", len(parsed_data["instruments"]))
            print("Total Gain:", parsed_data["total_gain"])
            print("Total Loss:", parsed_data["total_loss"])

            return parsed_data

        except Exception as e:
            print(f"Error in analyze_documents: {str(e)}")
            raise

    def _parse_results(self, results: List[str]) -> Dict:
        """Parse Claude's responses into structured data for K4 form"""
        trades = []
        total_gain = Decimal('0')
        total_loss = Decimal('0')

        # Regular expressions for parsing trade blocks
        trade_pattern = r'TRADE_START(.*?)TRADE_END'
        field_patterns = {
            'symbol': r'Symbol: (.+)',
            'description': r'Description: (.+)',
            'quantity': r'Quantity: (.+)',
            'sale_price': r'SalePriceSEK: (.+)',
            'purchase_price': r'PurchasePriceSEK: (.+)',
            'gain_loss': r'GainLossSEK: (.+)'
        }

        # Process each result chunk
        for result in results:
            # Find all trade blocks
            trade_blocks = re.finditer(trade_pattern, result, re.DOTALL)

            for trade_block in trade_blocks:
                trade_data = {}
                trade_text = trade_block.group(1)

                # Extract fields from trade block
                for field, pattern in field_patterns.items():
                    match = re.search(pattern, trade_text)
                    if match:
                        value = match.group(1).strip()
                        try:
                            if field in ['sale_price', 'purchase_price', 'gain_loss']:
                                value = Decimal(value.replace(',', ''))
                        except:
                            continue
                        trade_data[field] = value

                if trade_data:
                    trades.append(trade_data)

                    # Update totals
                    gain_loss = Decimal(str(trade_data.get('gain_loss', 0)))
                    if gain_loss > 0:
                        total_gain += gain_loss
                    else:
                        total_loss += gain_loss

        return {
            "instruments": trades,
            "total_gain": float(total_gain),
            "total_loss": float(total_loss)
        }


class K4FormFiller:
    def __init__(self, template_path: str):
        self.template_path = template_path

    def fill_form(self, data: Dict) -> io.BytesIO:
        """Fill K4 form with provided data"""
        reader = PdfReader(self.template_path)
        writer = PdfWriter()

        # Add all pages from template
        for page in reader.pages:
            writer.add_page(page)

        # Base form fields
        form_fields = {
            "Inkomstår": data.get('tax_year', datetime.now().year),
            "TxtPersOrgNr[0]": data.get('taxpayer_sin', ''),
            "TxtSkattskyldig-namn[0]": data.get('taxpayer_name', ''),
            "TxtDatFramst[0]": datetime.now().strftime("%Y-%m-%d")
        }

        # Add broker information if provided
        if data.get('broker_name'):
            form_fields["Depå"] = f"{data['broker_name']} - {data.get('account_number', '')}"

        # Fill section D with futures trades
        for idx, instrument in enumerate(data.get("instruments", []), start=0):
            if idx > 7:  # K4 form has 7 rows in section D
                print(f"Warning: More than 7 trades found. Extra trades will be omitted.")
                break

            # Format numbers to whole kronor
            sale_price = round(float(instrument['sale_price']))
            purchase_price = round(float(instrument['purchase_price']))
            gain_loss = round(float(instrument['gain_loss']))

            # Map to form fields
            description = f"{instrument['symbol']} - {instrument['description']}"

            form_fields.update({
                f"TxtAntal[{idx}]": str(instrument['quantity']),
                f"TxtBeteckning[{idx}]": description[:50],
                f"TxtForsaljningspris[{idx}]": str(sale_price),
                f"TxtOmkostnadsbelopp[{idx}]": str(purchase_price)
            })

            if gain_loss > 0:
                form_fields[f"TxtVinst[{idx}]"] = str(gain_loss)
            else:
                form_fields[f"TxtForlust[{idx}]"] = str(abs(gain_loss))

        # Update total fields
        if data.get("total_gain", 0) > 0:
            form_fields["TxtSummaVinst[0]"] = str(round(data["total_gain"]))
        if data.get("total_loss", 0) < 0:
            form_fields["TxtSummaForlust[0]"] = str(round(abs(data["total_loss"])))

        # Update all form fields
        for page_num in range(len(writer.pages)):
            writer.update_page_form_field_values(
                writer.pages[page_num],
                form_fields
            )

        # Write to buffer
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)

        return output_buffer

    def _get_actual_field_names(self) -> None:
        """Debug helper to print actual field names from the PDF form"""
        reader = PdfReader(self.template_path)
        for page_num, page in enumerate(reader.pages):
            if '/Annots' in page:
                for annot in page['/Annots']:
                    if annot.get_object()['/Subtype'] == '/Widget':
                        field_name = annot.get_object()['/T']
                        print(f"Page {page_num + 1} - Field name: {field_name}")

def process_and_fill_k4(
        statement_path: str,
        k4_template_path: str,
        claude_api_key: str
) -> io.BytesIO:
    """Main function to process statement and fill K4 form"""

    # Initialize processors
    doc_processor = K4DocumentProcessor(claude_api_key)
    form_filler = K4FormFiller(k4_template_path)

    try:
        # Process activity statement
        analysis_data = doc_processor.analyze_documents(statement_path)
        print(analysis_data)
        # Fill K4 form
        filled_form = form_filler.fill_form(analysis_data)

        return filled_form

    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        raise
