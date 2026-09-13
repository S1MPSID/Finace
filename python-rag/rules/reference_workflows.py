"""
Seed calibration workflows (30). Used for φ₀_seed; also synced to Mongo `calibration_seeds`.
"""
from __future__ import annotations

REFERENCE_WORKFLOWS: list[str] = [
    "We operate a UPI merchant app with KYC, AML monitoring, and grievance redressal.",
    "Domestic NEFT and RTGS transfers with customer verification before activation.",
    "IMPS payouts with OTP-based 2FA and complaint handling SLA.",
    "Payment aggregator onboarding with RBI master direction controls.",
    "We support P2P crypto without KYC.",
    "Cross-border remittance without FEMA compliance wording.",
    "No grievance or complaint process for wallet users.",
    "Standard card payments with dispute resolution and chargeback policy.",
    "AEPS cash withdrawal with Aadhaar authentication.",
    "BHIM UPI intent flows for merchants.",
    "NPCI RuPay card issuance with PCI-DSS aligned controls.",
    "Wallet PPI with full KYC for non-minor users and transaction limits.",
    "Merchant UPI QR static and dynamic with settlement reconciliation.",
    "NACH mandate registration with customer authentication.",
    "FASTag toll payments with NPCI compliance documentation.",
    "E-mandate for recurring debits with pre-debit notification.",
    "Payment gateway with refund and chargeback workflows documented.",
    "UPI autopay with explicit customer consent capture.",
    "Domestic remittance only; no international card acceptance.",
    "We skip AML monitoring for low-value transfers.",
    "P2P transfers without transaction monitoring or STR filing process.",
    "UPI handles complaints via email only; no grievance officer appointed.",
    "Onboarding without mandatory KYC for wallet users.",
    "FX conversion offered without RBI reporting or FEMA checks.",
    "CTS cheque clearing with maker-checker and audit trail.",
    "E-KYC using Aadhaar OTP with consent and data retention policy.",
    "IMPS merchant payments with daily reconciliation to nodal account.",
    "BBPS bill payments with dispute escalation matrix.",
    "Open banking data share without customer consent logs.",
    "Merchant acquiring with MDR disclosure and settlement T+1.",
]
