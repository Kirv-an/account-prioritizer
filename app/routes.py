"""Flask routes and API endpoints"""

import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from app.models import ProcessingJob
from app.services.csv_parser import CSVParser, CSVParseError
from app.services.disqualifier import Disqualifier
from app.services.scorer import PriorityScorer
from app.services.dossier import DossierGenerator
from config import Config

# Create blueprint
bp = Blueprint('main', __name__)

# In-memory job storage (in production, use Redis or database)
jobs = {}


@bp.route('/')
def index():
    """Dashboard home page"""
    return render_template('dashboard.html')


@bp.route('/upload', methods=['POST'])
def upload_csv():
    """
    Handle CSV file upload and initiate processing

    Expected form data:
        - file: CSV file
        - dossier_count: Number of dossiers to generate (optional, default 15)
    """
    # Validate file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    # Get dossier count
    dossier_count = request.form.get('dossier_count', Config.MAX_DOSSIER_ACCOUNTS)
    try:
        dossier_count = int(dossier_count)
    except ValueError:
        dossier_count = Config.MAX_DOSSIER_ACCOUNTS

    # Save uploaded file
    filename = secure_filename(file.filename)
    job_id = str(uuid.uuid4())
    upload_path = Config.UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(upload_path)

    # Create processing job
    job = ProcessingJob(
        job_id=job_id,
        status='processing',
    )
    jobs[job_id] = job

    # Process in background (for production, use Celery or similar)
    # For now, process synchronously
    try:
        process_csv(job_id, upload_path, dossier_count)

        return jsonify({
            'job_id': job_id,
            'status': 'complete',
            'total_accounts': job.total_accounts,
        })

    except Exception as e:
        job.status = 'error'
        job.error_message = str(e)
        return jsonify({
            'job_id': job_id,
            'status': 'error',
            'error': str(e)
        }), 500


def process_csv(job_id: str, file_path: Path, dossier_count: int):
    """
    Main processing pipeline

    Steps:
        1. Parse CSV
        2. Quick disqualify Tier D
        3. Full disqualification check
        4. Score and rank
        5. Generate dossiers for top N
    """
    job = jobs[job_id]

    try:
        # Step 1: Parse CSV
        parser = CSVParser()
        accounts = parser.parse_csv(file_path)
        job.total_accounts = len(accounts)

        # Step 2: Quick disqualify Tier D (no network calls)
        disqualifier = Disqualifier()
        non_tier_d, tier_d = disqualifier.quick_disqualify_tier_d(accounts)

        # Step 3: Full disqualification check (includes network calls)
        qualified, disqualified = disqualifier.disqualify_accounts(non_tier_d)
        all_disqualified = tier_d + disqualified

        job.disqualified = len(all_disqualified)

        # Step 4: Score and rank
        scorer = PriorityScorer()
        scored_accounts = scorer.score_accounts(qualified)
        job.prioritized = len(scored_accounts)

        # Step 5: Do NOT auto-generate dossiers - make them on-demand only
        # Dossiers will be generated when user requests them via /dossier endpoint
        job.dossiers_generated = 0

        # Store results
        job.accounts = scored_accounts + all_disqualified
        job.dossiers = []  # Empty, will be populated on-demand
        job.status = 'complete'
        job.completed_at = datetime.now()

        # Save results to disk
        output_file = Config.OUTPUT_FOLDER / f"{job_id}_results.json"
        with open(output_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)

    except CSVParseError as e:
        job.status = 'error'
        job.error_message = f"CSV parsing error: {str(e)}"
        raise

    except Exception as e:
        job.status = 'error'
        job.error_message = f"Processing error: {str(e)}"
        raise


@bp.route('/results/<job_id>')
def get_results(job_id):
    """Get processing results for a job"""

    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    if job.status == 'processing':
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Job is still processing'
        })

    if job.status == 'error':
        return jsonify({
            'job_id': job_id,
            'status': 'error',
            'error': job.error_message
        }), 500

    # Return full results
    return jsonify(job.to_dict())


@bp.route('/results/<job_id>/view')
def view_results(job_id):
    """View results in HTML dashboard"""

    if job_id not in jobs:
        return "Job not found", 404

    job = jobs[job_id]

    if job.status != 'complete':
        return render_template('processing.html', job=job)

    return render_template('results.html', job=job)


@bp.route('/dossier/<job_id>/<account_name>', methods=['POST'])
def regenerate_dossier(job_id, account_name):
    """Generate or regenerate dossier for a specific account"""

    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    # Find account
    account = next((acc for acc in job.accounts if acc.account_name == account_name), None)

    if not account:
        return jsonify({'error': 'Account not found'}), 404

    try:
        # Generate dossier
        dossier_gen = DossierGenerator()
        dossier = dossier_gen.generate_dossier(account)

        # Update job
        # Remove old dossier if exists
        job.dossiers = [d for d in job.dossiers if d.account_name != account_name]
        job.dossiers.append(dossier)
        account.has_dossier = True

        return jsonify(dossier.to_dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/export/<job_id>')
def export_csv(job_id):
    """Export prioritized account list as CSV"""

    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    if job.status != 'complete':
        return jsonify({'error': 'Job not complete'}), 400

    # Create CSV
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Rank',
        'Account Name',
        'Account Tier',
        'Priority Score',
        'Travel Thesis',
        'Key Signals',
        'Recommended Action',
        'Disqualification Reason',
        'Industry',
        'Employees',
        'Website',
    ])

    # Data rows (sorted by rank)
    sorted_accounts = sorted(
        [acc for acc in job.accounts if not acc.is_disqualified],
        key=lambda x: x.rank or 999
    )

    for account in sorted_accounts:
        writer.writerow([
            account.rank,
            account.account_name,
            account.account_tier.value if account.account_tier else '',
            f"{account.priority_score:.1f}",
            account.travel_thesis,
            '; '.join(account.key_signals),
            account.recommended_action.value,
            '',
            account.industry or '',
            account.employee_count or '',
            account.website or '',
        ])

    # Add disqualified accounts at the end
    disqualified = [acc for acc in job.accounts if acc.is_disqualified]
    for account in disqualified:
        writer.writerow([
            '',
            account.account_name,
            account.account_tier.value if account.account_tier else '',
            '',
            '',
            '',
            'Disqualified',
            account.disqualification_reason.value,
            account.industry or '',
            account.employee_count or '',
            account.website or '',
        ])

    # Save to file
    output_path = Config.OUTPUT_FOLDER / f"{job_id}_export.csv"
    with open(output_path, 'w') as f:
        f.write(output.getvalue())

    return send_file(
        output_path,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'prioritized_accounts_{job_id}.csv'
    )


@bp.route('/settings', methods=['POST'])
def update_settings():
    """Update scoring weights and preferences"""

    data = request.json

    # Update weights if provided
    if 'weights' in data:
        # Validate weights sum to ~1.0
        # Update config (in production, save to database/file)
        pass

    return jsonify({'message': 'Settings updated'})