"""
config.py — shared settings for the whole project.

Change the default file path, or the cost-column list, here — everything
else imports from this file so you only update it in one place.
"""

# Default data file. The dashboard's sidebar upload overrides this at runtime.
FILE = "Garment_12_updated.xlsx"

# Cost columns shared across the three daily production sheets.
# "Never used" columns (e.g. Security, SSGC) are kept here too: they're
# legitimate costs that just weren't recorded in *this* file — future data
# may populate them, so we don't drop them from the model.
COST_COLUMNS = [
    "Elect", "SSGC", "Fule", "Security", "Sweeper", "MIS", "Rent", "Transp",
    "Mechanic", "Helper/  Loader", "Chaker", "Supp", "QC", "Incharge", "HR/Acc",
]

# Component columns used in the per-product costing sheet (Sheet4).
PRODUCT_COST_COLUMNS = [
    "Cloth Amount/   peace", "Steaching/   peace",
    "embroidery/                                   peace",
    "washing/  Peace", "Cards & Leable", "Transport", "Mis",
]

# Mismatch tolerance in Rupees — differences smaller than this are treated
# as rounding, not real errors.
MISMATCH_TOLERANCE = 1.0