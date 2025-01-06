from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class ColumnDefinition:
    description: str
    hierarchy_level: Optional[int] = None
    distinct_values: List[str] = None

    def __post_init__(self):
        if self.distinct_values is None:
            self.distinct_values = []

class TableDefinition:
    def __init__(self, description: str, key_purposes: List[str], 
                 common_queries: List[str], relationships: Dict[str, str], 
                 columns: Dict[str, ColumnDefinition] = None):
        self.description = description
        self.key_purposes = key_purposes
        self.common_queries = common_queries
        self.relationships = relationships
        self.columns = columns or {}

class FinancialTableMetadata:
    def __init__(self):
        self.tables = {
            "final_income_sheet_new_seq": TableDefinition(
                description="Tracks revenue, expenses, and profitability over a period",
                key_purposes=[
                    "Monitor revenue and expenses",
                    "Track profitability",
                    "Compare actual vs budget"
                ],
                common_queries=[
                    "Revenue by type",
                    "Expense analysis",
                    "Profit margins",
                    "Common questions about the analysis"
                ],
                relationships={
                    "balance_sheet": "Impacts through P&L",
                    "forecast_sheet": "Actual vs forecast comparison"
                },
                columns = {
                    "Operator": ColumnDefinition(
                        description="Name of the operating entity or organization. Every operator manages multiple properties. hierarchy_level=1",
                        distinct_values=['Marriott', 'HHM', 'Remington', '24/7']
                    ),
                    "SQL_Property": ColumnDefinition(
                        description="List of hotel properties in the portfolio, including various brands and locations across the United States. Every property is managed by an operator. hierarchy_level=2",
                        distinct_values=['AC Wailea', 'Courtyard LA Pasadena Old Town', 'Courtyard Washington DC Dupont Circle', 'Hilton Garden Inn Bethesda', 'Marriott Crystal City', 'Moxy Washington DC Downtown', 'Residence Inn Pasadena', 'Residence Inn Westshore Tampa', 'Skyrock Inn Sedona', 'Steward Santa Barbara', 'Surfrider Malibu']
                    ),
                    "SQL_Account_Name": ColumnDefinition(
                        description="This column categorizes financial data into various account types, including operational data, reserves, income, expenses, profits, and fees. It also includes categories for non-operating income and expenses, as well as EBITDA. hierarchy_level=3",
                        distinct_values=['Operational Data', 'Replacement Reserve', 'Net Operating Income after Reserve', 'Revenue', 'Department Expenses', 'Department Profit (Loss', 'Undistributed Expenses', 'Gross Operating Profit', 'Management Fees', 'Income Before Non-Operating Inc & Exp', 'Non-Operating Income & Expenses', 'Total Non-Operating Income & Expenses', 'EBITDA', '-']
                    ),
                    "SQL_Account_Category_Order": ColumnDefinition(
                        description="Breakdown of (SQL_Account_Name) into more specific categories. Example: Under (Department Expense) from (SQL_Account_Name) there are 4 sub-categories in SQL_Account_Category_Order. hierarchy_level=4",
                        distinct_values=['Available Rooms', 'Rooms Sold', 'Occupancy %', 'Average Rate', 'RevPar', 'Replacement Reserve', 'NOI after Reserve', 'NOI Margin', 'Room Revenue', 'F&B Revenue', 'Other Revenue', 'Miscellaneous Income', 'Total Operating Revenue', 'Room Expense', 'F&B Expense', 'Other Expense', 'Total Department Expense', 'Department Profit (Loss)', 'A&G Expense', 'Information & Telecommunications', 'Sales & Marketing', 'Maintenance', 'Utilities', 'Total Undistributed Expenses', 'GOP', 'GOP Margin', 'Management Fees', 'Income Before Non-Operating Inc & Exp', 'Property & Other Taxes', 'Insurance', 'Other (Non-Operating I&E)', 'Total Non-Operating Income & Expenses', 'EBITDA']
                    ),
                    "Sub_Account_Category_Order": ColumnDefinition(
                        description="Breakdown of (SQL_Account_Category_Order) into more granular categorie. hierarchy_level=5",
                        distinct_values=['-', 'Replacement Reserve', 'EBITDA less REPLACEMENT RESERVE', 'Rooms', 'Food & Beverage', 'Other', 'Market', 'Rooms Other', 'Benefits/Bonus % Wages', 'Overtime Premium', 'Hourly Wages', 'Management Wages', 'FTG InRoom Services', 'Walked Guest', 'TA Commission', 'Cluster Reservation Cost', 'Comp F&B', 'Guest Supplies', 'Suite Supplies', 'Laundry', 'Cleaning Supplies', 'Linen', 'F&B Other', 'Service Charge Distribution', 'Beverage Cost', 'Food Cost', 'Other Sales Expense', 'Market Expense', 'A&G Other', 'Uniforms', 'Program Services Contribution', 'Transportation/Van Expense', 'Chargebacks', 'Employee Relations', 'Training', 'Postage', 'Bad Debt', 'Credit and Collection', 'Travel', 'Office Supplies', 'Pandemic Preparedness', 'Outside Labor Services', 'TOTAL I&TS CONT.', 'IT Compliance', 'FTG Internet', 'Guest Communications', 'Sales & Mkt. Other', 'Revenue Management', 'BT Booking Cost', 'Sales Shared Services', 'Loyalty', 'Marketing & eCommerce', 'Marketing Fund', 'PO&M Other', 'Cluster Engineering', 'PO&M NonContract', 'PO&M Contract', 'UTILITIES', 'Gross Operating Profit', 'Management Fees', 'Real Estate Tax', 'Over/Under Sales Tax', 'Property Insurance', 'Casualty Insurance', 'Other Investment Factors', 'Gain Loss Fx', 'Prior Year Adjustment', 'Lease Payments', 'Chain Services', 'Land Rent', 'Guest Accidents', 'Franchise Fees', 'System Fees', 'EBITDA', 'NOI after Reserve', 'Net Income', 'Other Operated Departments', 'Administrative & General', 'ADMINISTRATIVE & GENERAL', 'INFORMATION & TELECOMM.', 'Information & Telecommunications', 'FRANCHISE FEES', 'Sales & Marketing', 'Available Rooms', 'Property Operations & Maintenance', 'Utilities', 'Property & Other Taxes', 'Real Estate Property Tax', 'Personal Property Tax', 'Business Tax', 'Insurance - Property', 'Insurance General', 'Cyber Insurance', 'Employment Practices Insurance', 'Insurance', 'Professional Services', 'Legal & Accounting', 'Interest', 'Interest Expense-other', 'Lease Income', 'Total Food and Beverage', 'Total Other Operated Departments', 'Miscellaneous Income', 'Minor Ops', 'Franchise Taxes Owner', 'Other Expense', 'Total Other Operated Departments Expense', 'Miscellaneous Expense', 'Information & Telecommunications Sys.', 'MANAGEMENT FEE', 'REAL ESTATE/OTHER TAXES', 'HOTEL BED TAX CONTR', 'Property & Other taxes', 'Income', 'Rent & Leases', 'FFE Replacement Exp', 'Ownership Expense Owner', 'Depreciation and Amortization', 'Owner Expenses', 'EXTERNAL AUDIT FEES', 'DEFERRED MAINT. PRE-OPENING', 'COMMON AREA', 'Rent', 'RENT BASE', 'RENT VARIABLE', 'TRS LATE FEE', 'RATELOCK EXPENSE', 'BUDGET VARIANCE', 'CORPORATE OVERHEAD', 'OFFICE BLDG CASH FL', 'PROF SVCS-LEGAL', 'PROF SVCS', 'PROF SVCS-ENVIRONMENTAL', 'PROF SVCS-ACCOUNTING', 'PROF SVCS-OTHER', 'BAD DEBT EXPENSE', 'INCENTIVE MANAGEMENT FEE', 'PRE-OPENING EXPENSE', 'AMORTIZATION EXPENSE', 'OID W/O', 'PROCEEDS FROM CONVERSION', 'BASIS OF N/R', 'LONG TERM CAPITAL GAIN', 'OVERHEAD ALLOCATION', 'INTEREST EXPENSE', 'Asset Management Fee', 'Rent & Other Property/Equipment', 'Marketing Training', 'Prior Year Adj Tax', 'Property Tax', 'ASSET MANAGEMENT FEES', 'Management Fee Expense', 'NET OPERATING INCOME', 'ROOMS', 'FOOD & BEVERAGE', 'OTHER INCOME', 'SALES & MARKETING', 'REPAIRS & MAINTENANCE', 'PROPERTY TAX', 'PERSONAL PROPERTY TAX', 'LIABILITY INSURANCE', 'EQUIPMENT LEASES', "OWNER'S EXPENSE", 'LOAN INTEREST', 'ASSET MANAGEMENT FEE', 'REPLACEMENT RESERVES', 'Minibar', 'Mini Bar', 'Info & Telecom Systems', 'Property Operations', 'Interest Expense', 'Owner Expense', 'Reserve for Replacement']
                    ),
                    "SQL_Account_Group_Name": ColumnDefinition(
                        description="Further division of (Sub_Account_Category_Order). hierarchy_level=6",
                        distinct_values=['-', 'EBITDA less REPLACEMENT RESERVE', 'Rooms', 'Food & Beverage', 'Other', 'Guest Communications', 'Market', 'Rooms Other', 'Incentive Expense', 'Payroll Taxes', "Workers' Comp", 'Bonus', 'Medical', 'Overtime Premium', 'Hourly Wages', 'Management Wages', 'FTG InRoom Services', 'Walked Guest', 'TA Commission', 'Cluster Reservation Cost', 'Comp F&B', 'Guest Supplies', 'Suite Supplies', 'Laundry', 'Cleaning Supplies', 'Linen', 'F&B Other', 'Service Charge Distribution', 'Beverage Cost', 'Food Cost', 'Other Sales Expense', 'Market Expense', 'Uniforms', 'CAS System Support', 'Over/Short', 'A&G Other', 'Program Services Contribution', 'Transportation/Van Expense', 'Chargebacks', 'Employee Relations', 'Training', 'Postage', 'Bad Debt', 'Credit and Collection', 'Travel', 'Office Supplies', 'Pandemic Preparedness', 'Outside Labor Services', 'TOTAL I&TS CONT.', 'IT Compliance', 'FTG Internet', 'Sales Executive Share', 'Sales Exec Overhead Dept', 'Revenue Management', 'BT Booking Cost', 'Sales Shared Services', 'Loyalty', 'Marketing & eCommerce', 'Marketing Fund', 'PO&M Other', 'Cluster Engineering', 'PO&M NonContract', 'PO&M Contract', 'UTILITIES', 'Water/Sewer', 'Gas', 'Electricity', 'Gross Operating Profit', 'Real Estate Tax', 'Over/Under Sales Tax', 'Property Insurance', 'Casualty Insurance', 'Other Investment Factors', '71132 Common Area Chgs', 'Gain Loss Fx', 'Prior Year Adjustment', 'Lease Payments', 'Chain Services', 'Land Rent', 'Guest Accidents', 'Franchise Fees', 'System Fees', 'EBITDA', 'Marketing Training', 'Prior Year Adj Tax', 'Property Tax']
                    ),
                    "Current_Actual_Month": ColumnDefinition(
                        description="Actual financial performance for the month (income sheet). When a question is asked form the income sheet, use this column to do the aggregation/calculation for answering the queries"
                    ),
                    "YoY_Change": ColumnDefinition(
                        description="Percentage change compared to the same month in the prior year, computed for trend analysis"
                    ),
                    "Month": ColumnDefinition(
                        description="Time period for the data in YYYY-MM-DD format. When querying specific months (e.g., 'June 2024'), use format '2024-06-01' in SQL. Supports dates from January 2021 through October 2024. For month-specific queries, use strftime or date functions to match the format.",
                        distinct_values=['2024-10-01', '2024-08-01', '2024-09-01', '2024-07-01', '2024-06-01', '2024-04-01', '2022-11-01', '2024-05-01', '2022-05-01', '2022-03-01', '2022-02-01', '2021-12-01', '2023-03-01', '2023-01-01', '2023-04-01', '2023-02-01', '2024-01-01', '2023-12-01', '2024-02-01', '2022-12-01', '2022-10-01', '2023-10-01', '2023-09-01', '2023-08-01', '2023-11-01', '2022-08-01', '2022-06-01', '2022-04-01', '2022-07-01', '2022-09-01', '2022-01-01', '2021-11-01', '2021-10-01', '2021-08-01', '2023-06-01', '2023-05-01', '2023-07-01', '2021-09-01', '2024-03-01', '2021-05-01', '2021-06-01', '2021-07-01', '2021-03-01', '2021-04-01', '2021-02-01', '2021-01-01']
                    )
                }
            )
        }

    def get_table_info(self, table_name):
        return self.tables.get(table_name)

    def get_column_info(self, table_name, column_name):
        table = self.tables.get(table_name)
        if table:
            return table.columns.get(column_name)
        return None

    def get_metadata_prompt(self) -> str:
        """Generate a prompt with metadata information for the SQL agent"""
        prompt = "Database Schema Information:\n\n"
        for table_name, table in self.tables.items():
            prompt += f"Table: {table_name}\n"
            prompt += f"Description: {table.description}\n"
            prompt += "Key Purposes:\n" + "\n".join(f"- {purpose}" for purpose in table.key_purposes) + "\n"
            prompt += "Common Queries:\n" + "\n".join(f"- {query}" for query in table.common_queries) + "\n"
            prompt += "Relationships:\n"
            for related_table, relationship in table.relationships.items():
                prompt += f"- {related_table}: {relationship}\n"
            prompt += "\n"
        return prompt