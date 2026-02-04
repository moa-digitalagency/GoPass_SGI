from flask import Blueprint, request, make_response
from flask_login import login_required
from models import User, Airport, Airline, Transaction, Flight, GoPass
from services.finance_service import FinanceService
from services.export_service import ExportService
from sqlalchemy import or_

api_export_bp = Blueprint('api_export', __name__, url_prefix='/api/export')

@api_export_bp.route('/<entity_type>', methods=['GET'])
@login_required
def export_entity(entity_type):
    file_format = request.args.get('format', 'csv')

    data = []
    headers = []
    title = f"Export {entity_type.capitalize()}"

    if entity_type == 'users':
        search = request.args.get('search', '')
        role = request.args.get('role', '')

        query = User.query
        if search:
            query = query.filter(
                (User.username.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%')) |
                (User.first_name.ilike(f'%{search}%')) |
                (User.last_name.ilike(f'%{search}%'))
            )
        if role:
            query = query.filter_by(role=role)

        users = query.order_by(User.created_at.desc()).all()

        headers = ['ID', 'Nom Utilisateur', 'Email', 'Prénom', 'Nom', 'Rôle', 'Statut', 'Date Création']
        for u in users:
            data.append([
                u.id, u.username, u.email, u.first_name, u.last_name,
                u.role, 'Actif' if u.is_active else 'Inactif',
                u.created_at.strftime('%Y-%m-%d')
            ])

    elif entity_type == 'airports':
        search = request.args.get('search', '')
        country = request.args.get('country', '')
        type_ = request.args.get('type', '')

        query = Airport.query

        if search:
            query = query.filter(
                (Airport.name.ilike(f'%{search}%')) |
                (Airport.iata_code.ilike(f'%{search}%')) |
                (Airport.city.ilike(f'%{search}%'))
            )
        if country:
            query = query.filter(Airport.country == country)
        if type_:
            query = query.filter(Airport.type == type_)

        airports = query.order_by(Airport.iata_code).all()

        headers = ['Code IATA', 'Nom', 'Ville', 'Pays', 'Type']
        for a in airports:
            data.append([a.iata_code, a.name, a.city, a.country, a.type])

    elif entity_type == 'airlines':
        search = request.args.get('search', '')
        country = request.args.get('country', '')

        query = Airline.query

        if search:
            query = query.filter(
                (Airline.name.ilike(f'%{search}%')) |
                (Airline.iata_code.ilike(f'%{search}%')) |
                (Airline.icao_code.ilike(f'%{search}%'))
            )
        if country:
            query = query.filter(Airline.country == country)

        airlines = query.order_by(Airline.name).all()

        headers = ['Nom', 'IATA', 'ICAO', 'Pays', 'Actif']
        for a in airlines:
            data.append([
                a.name, a.iata_code, a.icao_code, a.country,
                'Oui' if a.is_active else 'Non'
            ])

    elif entity_type == 'transactions':
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

        headers = ['ID Transaction', 'Date', 'Type', 'Mode', 'Montant', 'Devise', 'Agent', 'Statut']
        for t in transactions:
            data.append([
                t.payment_ref or t.uuid,
                t.issue_date.strftime('%Y-%m-%d %H:%M') if t.issue_date else '',
                t.sales_channel,
                t.payment_method,
                t.price,
                t.currency,
                t.seller.username if t.seller else 'System',
                t.payment_status
            ])
        title = "Journal des Ventes"

    else:
        return "Type d'entité invalide", 400

    # Generate File
    if file_format == 'pdf':
        content = ExportService.generate_pdf(data, headers, title)
        mimetype = 'application/pdf'
        ext = 'pdf'
    else:
        content = ExportService.generate_csv(data, headers)
        mimetype = 'text/csv'
        ext = 'csv'

    response = make_response(content)
    response.headers['Content-Type'] = mimetype
    response.headers['Content-Disposition'] = f'attachment; filename=export_{entity_type}.{ext}'

    return response
