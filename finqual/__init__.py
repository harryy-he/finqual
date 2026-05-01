"""
finqual — financial research, analysis and comparable-company tooling for SEC EDGAR data.

Public API:
    Finqual       — fundamentals & ratios for a single company
    CCA           — comparable company analysis
    FinqualForms  — Form 4 (insider) and Form 13F (institutional) filings
"""

from .cca import CCA
from .core import Finqual
from .form_parsers import FinqualForms

__version__ = "4.8.1"

__all__ = ["CCA", "Finqual", "FinqualForms", "__version__"]
