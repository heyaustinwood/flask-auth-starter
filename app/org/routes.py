from flask import render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from app import db
from app.org import bp
from app.models import Organization, UserOrganization, User, Invitation
from app.auth.routes import require_org_permission
from sqlalchemy import func

@bp.route('/dashboard')
@login_required
@require_org_permission('member')
def dashboard():
    return render_template('org/dashboard.html')

@bp.route('/members', methods=['GET'])
@login_required
@require_org_permission('admin')
def members():
    members = UserOrganization.query.filter_by(organization_id=g.current_organization.id).all()
    # Filter invitations to only include those with status 'pending'
    invitations = Invitation.query.filter_by(organization_id=g.current_organization.id, status='pending').all()
    return render_template('org/members.html', members=members, invitations=invitations)

@bp.route('/remove-member/<int:user_id>', methods=['POST'])
@login_required
@require_org_permission('admin')
def remove_member(user_id):
    user_org = UserOrganization.query.filter_by(user_id=user_id, organization_id=g.current_organization.id).first()
    if user_org:
        db.session.delete(user_org)
        db.session.commit()
        flash('Member removed from the organization.')
    else:
        flash('Member not found in the organization.')
    return redirect(url_for('org.members'))

@bp.route('/change-role/<int:user_id>', methods=['POST'])
@login_required
@require_org_permission('admin')
def change_role(user_id):
    user_org = UserOrganization.query.filter_by(user_id=user_id, organization_id=g.current_organization.id).first()
    if user_org:
        new_role = request.form.get('role')
        if new_role in ['admin', 'member']:
            user_org.role = new_role
            db.session.commit()
            flash('Member role updated.')
        else:
            flash('Invalid role.')
    else:
        flash('Member not found in the organization.')
    return redirect(url_for('org.members'))

@bp.route('/revoke-invitation/<int:invitation_id>', methods=['POST'])
@login_required
@require_org_permission('admin')
def revoke_invitation(invitation_id):
    invitation = Invitation.query.filter_by(id=invitation_id, organization_id=g.current_organization.id).first()
    if invitation:
        invitation.status = 'revoked'  # Update status instead of deleting
        db.session.commit()
        flash('Invitation revoked successfully.', 'success')
    else:
        flash('Invitation not found.', 'error')
    return redirect(url_for('org.members'))
