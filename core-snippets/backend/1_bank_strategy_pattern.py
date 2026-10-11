import pandas as pd
from typing import Dict, Any
from abc import ABC, abstractmethod

# Note: This is an isolated snippet from the Brio AI backend demonstrating 
# the GoF Strategy and Factory patterns for dynamic CSV statement ingestion,
# including bank-specific parsers and a fuzzy-matching universal fallback parser.

# Strategy Pattern Abstract Base Parser
class BaseBankParser(ABC):
    """
    Abstract contract. Every bank integration must implement 
    the parse method and return a standardized dictionary for 
    the categorization pipeline.
    """
    @abstractmethod
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        pass

# Concrete Strategies (Parsers for specific banks)
class MonobankParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary normalization logic omitted for showcase
        return {
            "total_spent": 0.0,
            "total_income": 0.0,
            "currency_code": "UAH",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "transactions_for_ai": []
        }

class PrivatBankParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary normalization logic omitted for showcase
        return {
            "total_spent": 0.0,
            "total_income": 0.0,
            "currency_code": "UAH",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "transactions_for_ai": []
        }

class RaiffeisenParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary normalization logic omitted for showcase
        return {
            "total_spent": 0.0,
            "total_income": 0.0,
            "currency_code": "UAH",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "transactions_for_ai": []
        }

class UniversalUkrainianParser(BaseBankParser):
    """
    Fallback parser for any Ukrainian bank statement (CSV / XLSX).
    Applies fuzzy keyword matching with negative filters to dynamically map 
    arbitrary columns to the standardized schema: date, description, amount, 
    mcc (optional), and currency (optional).
    """
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Dynamic column detection and normalization logic omitted for showcase
        return {
            "total_spent": 0.0,
            "total_income": 0.0,
            "currency_code": "UAH",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "transactions_for_ai": []
        }

class UnknownBankFormatError(ValueError):
    """Raised when the uploaded file does not match any known bank schema or universal fallback."""
    pass

# Bank Sniffer & Factory
class BankSniffer:
    @staticmethod
    def detect(df: pd.DataFrame) -> str:
        """
        Analyzes DataFrame headers to automatically detect the bank origin.
        Prioritizes known bank schemas, then falls back to universal detection.
        """
        cols = [str(c).replace('\n', ' ').strip().lower() for c in df.columns]

        # 1. PrivatBank: matches specific card currency or transaction description headers
        if any(('опис операції' in c) or ('валюта' in c and 'картки' in c) for c in cols):
            return 'PRIVATBANK'
        
        # 2. Raiffeisen: matches transaction execution or account currency amount headers
        if any('здійснення операції' in c or 'сума у валюті рахунку' in c for c in cols):
            return 'RAIFFEISEN'

        # 3. Monobank: matches date combined with details/description headers
        if any('дата' in c for c in cols) and any('деталі' in c or 'опис' in c for c in cols):
            return 'MONOBANK'
        
        # 4. Universal Fallback: accepts files containing date + description + amount columns
        has_date = any('дата' in c or 'date' in c for c in cols)
        has_desc = any(kw in c for c in cols for kw in ['опис', 'деталі', 'призначення', 'descript', 'description', 'details'])
        has_amount = any(kw in c for c in cols for kw in ['сума', 'amount'])

        if has_date and has_desc and has_amount:
            return 'UNIVERSAL'
        
        # Guard clause against unsupported or random file uploads
        raise UnknownBankFormatError("Unsupported bank statement format. Could not detect bank type.")

class BankParserFactory:
    @staticmethod
    def get_parser(bank_type: str) -> BaseBankParser:
        if bank_type == 'MONOBANK':
            return MonobankParser()
        elif bank_type == 'PRIVATBANK':
            return PrivatBankParser()
        elif bank_type == 'RAIFFEISEN':
            return RaiffeisenParser()
        elif bank_type == 'UNIVERSAL':
            return UniversalUkrainianParser()
            
        raise ValueError(f"Unsupported bank type architecture: {bank_type}")