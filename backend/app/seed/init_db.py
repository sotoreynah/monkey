"""Initialize the database with tables, admin user, plan data, loans, and budget targets."""
from datetime import date, timedelta
from app.database import engine, SessionLocal, Base
from app.models import *  # noqa — imports all models so Base knows about them
from app.utils.security import hash_password
from app.config import get_settings


def init_database():
    settings = get_settings()

    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # --- Admin user ---
        existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not existing:
            user = User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
            )
            db.add(user)
            db.commit()
            print(f"Created admin user: {settings.ADMIN_USERNAME}")

        # --- Transaction sources ---
        sources = [
            ("Credit Card 6032", "credit_card", "6032", "US Bank"),
            ("Apple Card", "credit_card", None, "Apple/Goldman Sachs"),
            ("AMEX", "credit_card", "2003", "American Express"),
            ("Checking 1569", "checking", "1569", "US Bank"),
        ]
        for name, stype, last4, inst in sources:
            if not db.query(TransactionSource).filter(TransactionSource.name == name).first():
                db.add(TransactionSource(name=name, type=stype, last_four=last4, institution=inst))
        db.commit()

        # --- Financial Plan ---
        plan = db.query(FinancialPlan).filter(FinancialPlan.is_active == True).first()
        if not plan:
            plan = FinancialPlan(
                plan_name="Stop The Monkey",
                start_date=date(2026, 2, 2),
                end_date=date(2030, 12, 28),
                total_weeks=252,
                total_months=58,
                is_active=True,
            )
            db.add(plan)
            db.commit()
            db.refresh(plan)

            # --- Plan Phases ---
            phases = [
                (1, "Stop the Bleeding", 1, 6, 1, 26, "#EF4444",
                 "Emergency fund + 50% spending reduction",
                 "Build $1,000 starter emergency fund. Cut discretionary spending by 50%. Remove credit cards from auto-pay."),
                (2, "Debt Avalanche", 7, 24, 27, 104, "#F97316",
                 "Eliminate all non-mortgage debt",
                 "Pay off all credit cards, Affirm loans, auto loans, and personal loans using the avalanche method."),
                (3, "Build the Fortress", 25, 42, 105, 182, "#3B82F6",
                 "12-month emergency fund + max retirement",
                 "Build $156,000 emergency fund. Contribute 15% to retirement. Fund 529 plans."),
                (4, "Build the Runway", 43, 58, 183, 252, "#10B981",
                 "Accelerate mortgage + build runway",
                 "Extra mortgage principal payments. Build 12+ months of runway for potential job transition."),
            ]
            for pnum, name, sm, em, sw, ew, color, goal, desc in phases:
                db.add(PlanPhase(
                    plan_id=plan.id, phase_number=pnum, name=name,
                    start_month=sm, end_month=em, start_week=sw, end_week=ew,
                    color_code=color, primary_goal=goal, description=desc,
                ))
            db.commit()

            # --- Weekly Snapshots (252 weeks) ---
            plan_start = date(2026, 2, 2)
            for week_num in range(1, 253):
                week_start = plan_start + timedelta(weeks=week_num - 1)
                week_end = week_start + timedelta(days=6)
                if week_num <= 26:
                    phase = 1
                elif week_num <= 104:
                    phase = 2
                elif week_num <= 182:
                    phase = 3
                else:
                    phase = 4
                db.add(WeeklySnapshot(
                    plan_id=plan.id,
                    week_number=week_num,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    phase_number=phase,
                    status="future",
                ))
            db.commit()
            print("Created plan with 252 weekly snapshots")

        # --- Loans ---
        if not db.query(Loan).first():
            loans = [
                # Affirm BNPL
                ("Dyson", "bnpl", "Affirm", 970.18, 323.40, 0, 323.39, date(2026, 3, 1), 1, 1),
                ("Eight Sleep", "bnpl", "Affirm", 3157.47, 701.59, 0, 175.42, date(2026, 6, 2), 4, 2),
                ("Supernote", "bnpl", "Affirm", 721.18, 506.19, 0, 126.55, date(2026, 6, 11), 4, 3),
                ("Technogym", "bnpl", "Affirm", 5012.71, 1810.19, 0, 139.24, date(2027, 2, 14), 13, 4),
                ("Design Within Reach", "bnpl", "Affirm", 10266.86, 8555.72, 0, 855.57, date(2026, 12, 5), 10, 5),
                # Credit cards (balances approximate from plan)
                ("Credit Card 6032", "credit_card", "US Bank", None, 5000, 0.2299, 500, None, None, 6),
                ("AMEX", "credit_card", "American Express", None, 5742, 0.2199, 500, None, None, 7),
                ("Apple Card", "credit_card", "Goldman Sachs", None, 3000, 0.2499, 300, None, None, 8),
                # Auto loans
                ("VW Credit", "auto", "VW Credit Inc", None, 15000, 0.0599, 509, None, None, 9),
                ("Santander Consumer", "auto", "Santander", None, 12000, 0.0699, 420, None, None, 10),
                ("Tesla", "auto", "Tesla Finance", None, 25000, 0.0549, 775, None, None, 11),
                # Personal / Large
                ("LightStream", "personal", "LightStream/Truist", 60000, 60000, 0.0799, 1200, None, None, 12),
                ("German American Bank", "personal", "German American Bank", None, 80000, 0.0699, 2762, None, None, 13),
                # Mortgage
                ("Mortgage", "mortgage", "Heartland Bank", None, 350000, 0.0699, 3712, None, None, 99),
            ]
            for name, ltype, creditor, orig, balance, rate, payment, end, remaining, rank in loans:
                db.add(Loan(
                    name=name, loan_type=ltype, creditor=creditor,
                    original_amount=orig, current_balance=balance,
                    interest_rate=rate, monthly_payment=payment,
                    end_date=end, payments_remaining=remaining,
                    is_active=True, priority_rank=rank,
                ))
            db.commit()
            print("Seeded loans")

        # --- Budget Targets (Phase 1 from the plan) ---
        if not db.query(BudgetTarget).first():
            phase1_targets = [
                (1, "Mortgage", 3712, True),
                (1, "Auto Loan", 1704, True),  # VW + Santander + Tesla
                (1, "BNPL Payment", 1120, True),
                (1, "Personal Loan", 3962, True),  # German American + LightStream
                (1, "CC Payment", 1500, True),
                (1, "Airlines/Travel", 100, False),
                (1, "Entertainment", 100, False),
                (1, "Dining", 150, False),
                (1, "Shopping", 100, False),
                (1, "Clothing", 50, False),
                (1, "Furnishing", 0, False),
                (1, "Fitness", 150, False),
                (1, "Groceries", 700, False),
                (1, "Subscriptions", 60, False),
                (1, "Investing", 0, False),
                (1, "Remittances", 376, True),
                (1, "Cash", 100, False),
                (1, "Other", 200, False),
            ]
            for phase, cat, target, fixed in phase1_targets:
                db.add(BudgetTarget(
                    phase_number=phase, category=cat,
                    monthly_target=target, is_fixed=fixed,
                ))
            db.commit()
            print("Seeded Phase 1 budget targets")

        # --- Milestones ---
        if not db.query(Milestone).first():
            milestones = [
                (1, "Baby Step 1: $1,000 Emergency Fund", "$1,000 in separate savings", date(2026, 2, 28), 1000),
                (1, "Remove CCs from Apple Pay & Amazon", "Freeze all credit cards", date(2026, 2, 14), None),
                (1, "Cancel extra gym memberships", "Keep ONE fitness membership", date(2026, 2, 21), None),
                (1, "Switch groceries to Kroger/Costco", "Reduce grocery spend 30-40%", date(2026, 3, 1), None),
                (1, "50% spending reduction achieved", "Monthly spend under $13,000", date(2026, 7, 31), 13000),
                (2, "All Affirm loans paid off", "5 BNPL loans eliminated", date(2027, 2, 28), 0),
                (2, "All credit card debt eliminated", "CC balances at $0", date(2027, 6, 30), 0),
                (2, "All non-mortgage debt eliminated", "Baby Step 2 complete", date(2028, 1, 31), 0),
                (3, "12-month emergency fund", "$156,000 in HYSA", date(2029, 7, 31), 156000),
                (3, "15% retirement contributions", "Max 401k + Roth IRA", date(2028, 6, 30), 38400),
                (4, "12+ months runway built", "Ready for job transition", date(2030, 12, 31), 156000),
            ]
            for phase, name, desc, target_date, amount in milestones:
                db.add(Milestone(
                    phase_number=phase, name=name, description=desc,
                    target_date=target_date, target_amount=amount,
                ))
            db.commit()
            print("Seeded milestones")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
