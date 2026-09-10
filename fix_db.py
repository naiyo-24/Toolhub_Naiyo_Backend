from database import engine, Base
import models.tool
import models.user
import models.business
import models.forms
import models.contact
import models.organization
import models.customer
import models.loan_case
import models.bank_statement
import models.document
import models.ocr_result
import models.financial_analysis
import models.risk_analysis
import models.report
import models.task
import models.verification
import models.banker_profile
import models.account_deletion
import models.case_event
import models.loan_calculation
import models.notification

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
