from app.core.database import SessionLocal
from app.models.models import Folio, Payment
from decimal import Decimal

db = SessionLocal()

folio_id = "397c53e4-de60-40bc-9c31-1ed6082edc7d"
folio = db.query(Folio).filter(Folio.id == folio_id).first()

actual_total_payments = sum(Decimal(str(p.amount)) for p in db.query(Payment).filter(Payment.folio_id == folio_id).all())

print(f"Before: total_payments={folio.total_payments}, balance={folio.balance}")

folio.total_payments = actual_total_payments
folio.balance = Decimal(str(folio.total_charges)) - actual_total_payments
if folio.balance < 0:
    folio.balance = Decimal("0")

db.commit()

print(f"After: total_payments={folio.total_payments}, balance={folio.balance}")

db.close()