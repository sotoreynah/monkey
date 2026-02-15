"""
Debt Payoff Calculator Service
Implements debt avalanche algorithm (highest interest rate first)
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.plan import FinancialPlan


class DebtPayoffCalculator:
    """Calculate debt payoff timeline using debt avalanche method"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_payoff_plan(
        self, 
        loans: List[Loan], 
        monthly_capacity: float,
        start_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate complete debt payoff timeline
        
        Args:
            loans: List of active loans
            monthly_capacity: Total monthly payment capacity
            start_date: Starting date for calculation (defaults to today)
        
        Returns:
            Dictionary with summary, payoff_order, and timeline
        """
        if start_date is None:
            start_date = date.today()
        
        # Clone loans to avoid modifying originals
        working_loans = []
        for loan in loans:
            if loan.is_active and loan.current_balance > 0:
                working_loans.append({
                    'id': loan.id,
                    'name': loan.name,
                    'balance': float(loan.current_balance),
                    'rate': float(loan.interest_rate) if loan.interest_rate else 0.0,
                    'minimum_payment': float(loan.monthly_payment) if loan.monthly_payment else 0.0,
                    'priority_rank': loan.priority_rank if loan.priority_rank else 999,
                    'total_interest_paid': 0.0  # Track interest per loan
                })
        
        # Sort by priority rank (lower number = higher priority = pay first)
        working_loans.sort(key=lambda x: x['priority_rank'])
        
        # Calculate totals
        total_debt = sum(loan['balance'] for loan in working_loans)
        total_minimum = sum(loan['minimum_payment'] for loan in working_loans)
        
        # Warning flag if capacity is below minimums (user is underwater)
        is_underwater = monthly_capacity < total_minimum
        
        # If underwater, we'll still calculate but it will take a VERY long time
        # Use the capacity they have and warn them
        effective_capacity = monthly_capacity
        
        # Track payoffs
        payoff_order = []
        timeline = []
        current_month = 0
        current_date = start_date
        total_interest_paid = 0
        
        while any(loan['balance'] > 0 for loan in working_loans):
            current_month += 1
            monthly_interest = 0
            monthly_principal = 0
            
            # Step 1: Apply interest to all loans
            for loan in working_loans:
                if loan['balance'] > 0:
                    monthly_rate = loan['rate'] / 12
                    interest = loan['balance'] * monthly_rate
                    loan['balance'] += interest
                    loan['total_interest_paid'] += interest  # Track per loan
                    monthly_interest += interest
            
            # Step 2: Pay what we can (minimums if possible, proportional if not)
            remaining_payment = monthly_capacity
            
            if is_underwater:
                # Underwater: Pay proportionally across all loans
                # This won't be enough, but shows the user what happens
                for loan in working_loans:
                    if loan['balance'] > 0 and remaining_payment > 0:
                        # Pay proportionally based on minimum payment ratios
                        loan_ratio = loan['minimum_payment'] / total_minimum if total_minimum > 0 else 0
                        payment = min(remaining_payment * loan_ratio, loan['balance'])
                        loan['balance'] -= payment
                        monthly_principal += payment
                        remaining_payment -= payment
            else:
                # Normal: Pay minimums on all loans
                for loan in working_loans:
                    if loan['balance'] > 0:
                        minimum = min(loan['minimum_payment'], loan['balance'], remaining_payment)
                        loan['balance'] -= minimum
                        monthly_principal += minimum
                        remaining_payment -= minimum
            
            # Step 3: Apply extra to highest priority loan
            for loan in working_loans:
                if loan['balance'] > 0 and remaining_payment > 0:
                    extra = min(remaining_payment, loan['balance'])
                    loan['balance'] -= extra
                    monthly_principal += extra
                    remaining_payment -= extra
                    break  # Only apply extra to one loan at a time
            
            # Step 4: Check which loans were paid off this month
            paid_off_loan_ids = {lo['loan_id'] for lo in payoff_order}
            for loan in working_loans:
                if loan['balance'] <= 0.01 and loan['id'] not in paid_off_loan_ids:
                    # Loan just paid off this month
                    loan['balance'] = 0
                    payoff_order.append({
                        'rank': len(payoff_order) + 1,
                        'loan_id': loan['id'],
                        'name': loan['name'],
                        'payoff_month': current_month,
                        'payoff_date': current_date.isoformat(),
                        'interest_paid': round(loan['total_interest_paid'], 2)
                    })
            
            # Track timeline
            total_interest_paid += monthly_interest
            debt_remaining = sum(loan['balance'] for loan in working_loans)
            
            timeline.append({
                'month': current_month,
                'month_date': current_date.isoformat(),
                'total_debt_remaining': round(debt_remaining, 2),
                'total_paid': round(monthly_capacity, 2),
                'interest_portion': round(monthly_interest, 2),
                'principal_portion': round(monthly_principal, 2),
                'active_loan': next(
                    (loan['name'] for loan in working_loans if loan['balance'] > 0),
                    'All paid off'
                )
            })
            
            # Move to next month
            current_date += relativedelta(months=1)
            
            # Safety check (max 600 months = 50 years)
            if current_month > 600:
                # If underwater, debt will never be paid off
                if is_underwater:
                    break  # Stop calculating, return what we have
                raise ValueError("Calculation exceeded 50 years - check inputs")
            
            # Check if debt is growing instead of shrinking
            if current_month > 1 and debt_remaining > total_debt:
                # Debt is growing - stop here
                break
        
        # Calculate summary
        debt_free_date = current_date
        months_to_debt_free = current_month
        
        # Check if debt was paid off or if we hit limits
        final_debt_remaining = sum(loan['balance'] for loan in working_loans)
        debt_paid_off = final_debt_remaining < 1.0
        
        # Calculate interest saved (compare to minimum payments forever)
        # Simple estimate: if paying only minimums, how much interest?
        total_minimum_only_interest = sum(
            loan['balance'] * loan['rate'] * 0.5  # Rough estimate
            for loan in working_loans
        )
        interest_saved = max(0, total_minimum_only_interest - total_interest_paid)
        
        # Generate appropriate warning
        warning_message = None
        if is_underwater:
            if debt_paid_off:
                # Making progress but slower than normal
                warning_message = (
                    f"⚠️ Monthly capacity (${monthly_capacity:,.2f}) is less than "
                    f"minimum payments (${total_minimum:,.2f}). "
                    f"You'll pay off your debt, but it will take significantly longer "
                    f"and cost more in interest. Consider increasing payments to at least "
                    f"${total_minimum:,.2f} to accelerate payoff."
                )
            else:
                # Truly underwater - debt growing
                warning_message = (
                    f"🚨 Monthly capacity (${monthly_capacity:,.2f}) is less than "
                    f"minimum payments (${total_minimum:,.2f}). At this payment level, "
                    f"your debt will continue to grow. Increase your monthly capacity to "
                    f"at least ${total_minimum:,.2f} to start making progress."
                )
        
        summary = {
            'total_debt': round(total_debt, 2),
            'monthly_capacity': round(monthly_capacity, 2),
            'total_minimum_payments': round(total_minimum, 2),
            'months_to_debt_free': months_to_debt_free if debt_paid_off else None,
            'debt_free_date': debt_free_date.isoformat() if debt_paid_off else None,
            'total_interest_paid': round(total_interest_paid, 2),
            'interest_saved': round(interest_saved, 2),
            'total_paid': round(total_debt + total_interest_paid, 2),
            'is_underwater': is_underwater,
            'debt_paid_off': debt_paid_off,
            'remaining_debt': round(final_debt_remaining, 2) if not debt_paid_off else 0,
            'warning': warning_message
        }
        
        return {
            'summary': summary,
            'payoff_order': payoff_order,
            'timeline': timeline
        }
    
    def recalculate_for_plan(self, plan_id: int) -> Dict[str, Any]:
        """
        Recalculate debt payoff for a specific plan
        Uses the plan's monthly_payment_capacity and active loans
        """
        plan = self.db.query(FinancialPlan).filter(FinancialPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        loans = self.db.query(Loan).filter(Loan.is_active == True).all()
        
        return self.calculate_payoff_plan(
            loans=loans,
            monthly_capacity=plan.monthly_payment_capacity,
            start_date=plan.start_date
        )
