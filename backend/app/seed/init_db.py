"""Initialize the database with tables, admin user, plan data, and milestones."""
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
            ("Credit Card A", "credit_card", "XXXX", "Bank A"),
            ("Credit Card B", "credit_card", None, "Bank B"),
            ("Credit Card C", "credit_card", "XXXX", "Bank C"),
            ("Checking", "checking", "XXXX", "Bank A"),
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
                 "Emergency fund + spending reduction",
                 "Build starter emergency fund. Cut discretionary spending. Remove credit cards from auto-pay."),
                (2, "Debt Avalanche", 7, 24, 27, 104, "#F97316",
                 "Eliminate all non-mortgage debt",
                 "Pay off all credit cards, BNPL loans, auto loans, and personal loans using the avalanche method."),
                (3, "Build the Fortress", 25, 42, 105, 182, "#3B82F6",
                 "12-month emergency fund + max retirement",
                 "Build full emergency fund. Contribute 15% to retirement. Fund education savings."),
                (4, "Build the Runway", 43, 58, 183, 252, "#10B981",
                 "Accelerate mortgage + build runway",
                 "Extra mortgage principal payments. Build 12+ months of runway for potential career transition."),
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

        # --- Milestones ---
        if not db.query(Milestone).first():
            milestones = [
                (1, "Starter Emergency Fund", "Build initial emergency fund", date(2026, 2, 28), 1000),
                (1, "Freeze credit cards", "Remove cards from digital wallets", date(2026, 2, 14), None),
                (1, "Cancel unnecessary subscriptions", "Keep only essential services", date(2026, 2, 21), None),
                (1, "Reduce grocery spending", "Switch to budget-friendly stores", date(2026, 3, 1), None),
                (1, "Spending reduction achieved", "Hit monthly spending target", date(2026, 7, 31), None),
                (2, "All BNPL loans paid off", "BNPL loans eliminated", date(2027, 2, 28), 0),
                (2, "All credit card debt eliminated", "CC balances at $0", date(2027, 6, 30), 0),
                (2, "All non-mortgage debt eliminated", "Debt avalanche complete", date(2028, 1, 31), 0),
                (3, "Full emergency fund", "12 months expenses in HYSA", date(2029, 7, 31), None),
                (3, "15% retirement contributions", "Max retirement accounts", date(2028, 6, 30), None),
                (4, "12+ months runway built", "Ready for career transition", date(2030, 12, 31), None),
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
