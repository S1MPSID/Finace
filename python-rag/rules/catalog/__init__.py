"""Deterministic regex rule packs by payment / regulatory category."""

from rules.catalog.core_controls import CORE_RULES
from rules.catalog.upi_rules import UPI_RULES
from rules.catalog.imps_rules import IMPS_RULES
from rules.catalog.aeps_rules import AEPS_RULES
from rules.catalog.neft_rtgs_rules import NEFT_RTGS_RULES
from rules.catalog.cts_rules import CTS_RULES
from rules.catalog.ekyc_rules import EKYC_RULES
from rules.catalog.nfs_rules import NFS_RULES
from rules.catalog.npci_rules import NPCI_RULES
from rules.catalog.rbi_md_rules import RBI_MD_RULES
from rules.catalog.crypto_rules import CRYPTO_RULES
from rules.catalog.fema_rules import FEMA_RULES

ALL_CATALOG_RULES: list[dict] = [
    *CORE_RULES,
    *UPI_RULES,
    *IMPS_RULES,
    *AEPS_RULES,
    *NEFT_RTGS_RULES,
    *CTS_RULES,
    *EKYC_RULES,
    *NFS_RULES,
    *NPCI_RULES,
    *RBI_MD_RULES,
    *CRYPTO_RULES,
    *FEMA_RULES,
]
