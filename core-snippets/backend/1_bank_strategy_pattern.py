import pandas as pd
from typing import Dict, Any
from abc import ABC, abstractmethod

# Note: This is an isolated snippet from the Brio AI backend demonstrating 
# the GoF Strategy and Factory patterns for dynamic CSV statement ingestion.

# Strategy Pattern Abstract Base Parser
class BaseBankParser(ABC):
    """
    Abstract contract. Every new bank integration
    must implement the parse method and return a 
    standardized dictionary for the categorization pipeline.
    """
    @abstractmethod
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        pass

# Concrete Strategies (Parsers for specific banks)
class MonobankParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary parsing and normalization logic omitted for showcase
        return {"bank": "monobank", "transactions": []}

class PrivatBankParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary parsing and normalization logic omitted for showcase
        return {"bank": "privatbank", "transactions": []}

class RaiffeisenParser(BaseBankParser):
    def parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Proprietary parsing and normalization logic omitted for showcase
        return {"bank": "raiffeisen", "transactions": []}

class UnknownBankFormatError(ValueError):
    """Raised when the uploaded file does not match any known bank schema."""
    pass

# Bank Sniffer & Factory
class BankSniffer:
    @staticmethod
    def detect(df: pd.DataFrame) -> str:
        """
        Analyzes DataFrame headers to automatically detect the bank origin.
        """
        cols = [str(c).replace('\n', ' ').strip().lower() for c in df.columns]

        if any('опис операції' in c or ('валюта' in c and 'картки' in c) for c in cols):
            return 'PRIVATBANK'
        
        if any('здійснення операції' in c or 'сума у валюті рахунку' in c for c in cols):
            return 'RAIFFEISEN'

        if any('дата' in c for c in cols) and any('деталі' in c or 'опис' in c for c in cols):
            return 'MONOBANK'
        
        # Guard clause against random file uploads
        raise UnknownBankFormatError("Could not detect a supported bank format in the uploaded statement.")

class BankParserFactory:
    @staticmethod
    def get_parser(bank_type: str) -> BaseBankParser:
        if bank_type == 'MONOBANK':
            return MonobankParser()
        elif bank_type == 'PRIVATBANK':
            return PrivatBankParser()
        elif bank_type == 'RAIFFEISEN':
            return RaiffeisenParser()
            
        raise ValueError(f"Unsupported bank type architecture: {bank_type}")