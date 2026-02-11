"""
* Nom de l'application : GoPass SGI-GP
 * Description : Logic and implementation for finance_service.py
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""

from models import db, GoPass, CashDeposit, MobileMoneyLog, User, PassType
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import csv
import io

class FinanceService:
    @staticmethod
    def get_transactions(start_date=None, end_date=None, agent_id=None, payment_method=None, sales_channel=None):
        query = GoPass.query

        if start_date:
            # Ensure start_date is a datetime object or parse it
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(GoPass.issue_date >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end date to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(GoPass.issue_date <= end_date)

        if agent_id:
            query = query.filter(GoPass.sold_by == agent_id)

        if payment_method:
            query = query.filter(GoPass.payment_method == payment_method)

        if sales_channel:
             query = query.filter(GoPass.sales_channel == sales_channel)

        # Order by newest first
        return query.order_by(GoPass.issue_date.desc()).all()

    @staticmethod
    def get_agent_balances():
        # Get all agents
        agents = User.query.filter_by(role='agent').all()
        balances = []

        for agent in agents:
            # Theoretical Sales (Cash only)
            sales_total = db.session.query(func.sum(GoPass.price))\
                .filter(GoPass.sold_by == agent.id)\
                .filter(GoPass.payment_method == 'Cash')\
                .filter(GoPass.payment_status == 'paid')\
                .scalar() or 0.0

            # Deposited Amount
            deposited_total = db.session.query(func.sum(CashDeposit.amount))\
                .filter(CashDeposit.agent_id == agent.id)\
                .scalar() or 0.0

            balance = sales_total - deposited_total

            balances.append({
                'agent': agent,
                'sales_total': sales_total,
                'deposited_total': deposited_total,
                'balance': balance,
                'status': 'balanced' if abs(balance) < 0.01 else 'discrepancy'
            })

        return balances

    @staticmethod
    def record_deposit(agent_id, supervisor_id, amount, notes=''):
        deposit = CashDeposit(
            agent_id=agent_id,
            supervisor_id=supervisor_id,
            amount=amount,
            notes=notes
        )
        db.session.add(deposit)
        db.session.commit()
        return deposit

    @staticmethod
    def get_reconciliation():
        # Get all Mobile Money Passes
        mm_passes = GoPass.query.filter(GoPass.payment_method.in_(['M-Pesa', 'Airtel', 'Orange'])).all()

        # Get all Mobile Money Logs
        mm_logs = MobileMoneyLog.query.all()

        # Map logs by transaction_ref
        log_map = {log.transaction_ref: log for log in mm_logs}

        reconciliation_data = []

        # Check Passes vs Logs
        for gp in mm_passes:
            log = log_map.get(gp.payment_ref)
            status = 'matched'
            discrepancy = 0.0

            if not log:
                status = 'missing_in_provider'
            elif log.amount != gp.price:
                status = 'amount_mismatch'
                discrepancy = gp.price - log.amount
            elif log.status != 'success':
                status = 'provider_failed'

            reconciliation_data.append({
                'type': 'pass',
                'id': gp.id,
                'date': gp.issue_date,
                'ref': gp.payment_ref,
                'amount_sys': gp.price,
                'amount_provider': log.amount if log else 0.0,
                'provider': gp.payment_method,
                'status': status,
                'discrepancy': discrepancy,
                'color': 'green' if status == 'matched' else 'red'
            })

        # Check Logs vs Passes (Orphans)
        pass_refs = {gp.payment_ref for gp in mm_passes}
        for log in mm_logs:
            if log.transaction_ref not in pass_refs:
                reconciliation_data.append({
                    'type': 'log',
                    'id': log.id,
                    'date': log.timestamp,
                    'ref': log.transaction_ref,
                    'amount_sys': 0.0,
                    'amount_provider': log.amount,
                    'provider': log.provider,
                    'status': 'missing_in_system',
                    'discrepancy': -log.amount,
                    'color': 'orange'
                })

        return reconciliation_data

    @staticmethod
    def export_to_csv(data, headers, filename):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def calculate_flight_price(flight, target_currency='USD'):
        from services.settings_service import SettingsService
        from services.flight_service import FlightService
        from models import Airport

        # Get System Region (e.g. 'CD')
        settings = SettingsService.get_general_settings()
        system_region = settings.get('region', 'CD')

        dep_country = None
        arr_country = None

        if isinstance(flight, dict):
            # API Data
            dep_country = flight.get('departure', {}).get('country_iso2')
            arr_country = flight.get('arrival', {}).get('country_iso2')
        else:
            # SQLAlchemy Model
            dep_airport = Airport.query.filter_by(iata_code=flight.departure_airport).first()
            if dep_airport:
                dep_country = dep_airport.country
            elif flight.departure_airport in FlightService.CONGOLESE_AIRPORTS:
                dep_country = 'CD'

            arr_airport = Airport.query.filter_by(iata_code=flight.arrival_airport).first()
            if arr_airport:
                arr_country = arr_airport.country
            elif flight.arrival_airport in FlightService.CONGOLESE_AIRPORTS:
                arr_country = 'CD'

        # Determine Base Price (USD)
        price_dom = float(SettingsService.get_config('price_domestic', 15.0))
        price_int = float(SettingsService.get_config('price_international', 55.0))

        price = price_int
        # Logic: If both are system_region (e.g. CD), then Domestic.
        # Default to International if country info is missing
        if dep_country == system_region and arr_country == system_region:
            price = price_dom

        # Convert Currency
        if target_currency == 'USD':
            return price

        # Get rate
        rates = settings.get('rates', {})
        rate = float(rates.get(target_currency, 1.0))

        return round(price * rate, 2)
