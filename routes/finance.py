from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
from services.finance_service import FinanceService
from models import User
from datetime import datetime

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

@finance_bp.route('/transactions')
@login_required
def transactions():
    if current_user.role not in ['admin', 'agent', 'controller']:
        flash("Accès non autorisé", "danger")
        return redirect(url_for('dashboard.index'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    agent_id = request.args.get('agent_id')
    payment_method = request.args.get('payment_method')

    transactions = FinanceService.get_transactions(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id,
        payment_method=payment_method
    )

    agents = User.query.filter_by(role='agent').all()

    return render_template('finance/transactions.html',
                           transactions=transactions,
                           agents=agents,
                           start_date=start_date,
                           end_date=end_date,
                           selected_agent=int(agent_id) if agent_id else None,
                           selected_method=payment_method)

@finance_bp.route('/deposits', methods=['GET', 'POST'])
@login_required
def deposits():
    if current_user.role not in ['admin']: # Only Admin (Supervisor) can see/manage this
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        agent_id = request.form.get('agent_id')
        amount = float(request.form.get('amount', 0))
        notes = request.form.get('notes')

        FinanceService.record_deposit(agent_id, current_user.id, amount, notes)
        flash("Versement enregistré avec succès", "success")
        return redirect(url_for('finance.deposits'))

    balances = FinanceService.get_agent_balances()
    return render_template('finance/deposits.html', balances=balances)

@finance_bp.route('/reconciliation')
@login_required
def reconciliation():
    if current_user.role not in ['admin']:
        flash("Accès réservé aux administrateurs", "danger")
        return redirect(url_for('dashboard.index'))

    data = FinanceService.get_reconciliation()
    return render_template('finance/reconciliation.html', reconciliation_data=data)

@finance_bp.route('/export/<report_type>')
@login_required
def export_data(report_type):
    if report_type == 'transactions':
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        agent_id = request.args.get('agent_id')
        payment_method = request.args.get('payment_method')

        data = FinanceService.get_transactions(start_date, end_date, agent_id, payment_method)
        rows = []
        for t in data:
            rows.append([
                t.payment_ref or t.id,
                t.issue_date,
                t.sales_channel,
                t.payment_method,
                t.price,
                t.seller.username if t.seller else 'System',
                t.payment_status
            ])
        headers = ['ID Transaction', 'Date', 'Type', 'Mode', 'Montant', 'Agent', 'Statut']
        csv_data = FinanceService.export_to_csv(rows, headers, 'transactions.csv')
        filename = f'transactions_{datetime.now().strftime("%Y%m%d%H%M")}.csv'

    elif report_type == 'deposits':
        data = FinanceService.get_agent_balances()
        rows = []
        for b in data:
            rows.append([
                b['agent'].username,
                b['sales_total'],
                b['deposited_total'],
                b['balance'],
                b['status']
            ])
        headers = ['Agent', 'Ventes Théoriques', 'Total Versé', 'Solde/Écart', 'Statut']
        csv_data = FinanceService.export_to_csv(rows, headers, 'deposits.csv')
        filename = f'deposits_{datetime.now().strftime("%Y%m%d%H%M")}.csv'

    elif report_type == 'reconciliation':
        data = FinanceService.get_reconciliation()
        rows = []
        for r in data:
            rows.append([
                r['type'],
                r['id'],
                r['date'],
                r['ref'],
                r['amount_sys'],
                r['amount_provider'],
                r['provider'],
                r['status'],
                r['discrepancy']
            ])
        headers = ['Type', 'ID', 'Date', 'Ref', 'Montant Sys', 'Montant Prov', 'Provider', 'Statut', 'Ecart']
        csv_data = FinanceService.export_to_csv(rows, headers, 'reconciliation.csv')
        filename = f'reconciliation_{datetime.now().strftime("%Y%m%d%H%M")}.csv'

    else:
        return "Type de rapport invalide", 400

    output = make_response(csv_data)
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output
