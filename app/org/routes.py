from flask import render_template, redirect, url_for, flash, request, g, current_app
from flask_login import login_required, current_user
from app import db
from app.org import bp
from app.models import Organization, UserOrganization, User, Invitation
from app.auth.routes import require_org_permission
from sqlalchemy import func

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        # Fetch the organization directly using the current_user's current_organization_id
        g.current_organization = Organization.query.get(current_user.current_organization_id)
    else:
        g.current_organization = None

@bp.route('/dashboard')
@login_required
@require_org_permission('member')
def dashboard():
    if not g.current_organization:
        flash('Please select or create an organization first.')
        return redirect(url_for('auth.select_organization'))
    return render_template('org/dashboard.html', organization=g.current_organization)

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
    if user_id == current_user.id:
        flash('You cannot remove yourself from an organization.')
        return redirect(url_for('org.members'))

    # Count the total number of members and admins in the organization
    member_count = UserOrganization.query.filter_by(organization_id=g.current_organization.id).count()
    admin_count = UserOrganization.query.filter_by(
        organization_id=g.current_organization.id,
        role='admin'
    ).count()

    user_org = UserOrganization.query.filter_by(
        user_id=user_id,
        organization_id=g.current_organization.id
    ).first()

    if not user_org:
        flash('Member not found in the organization.')
        return redirect(url_for('org.members'))

    if member_count <= 1:
        flash('You cannot remove the last member from an organization. Every organization has to have at least 1 member.')
        return redirect(url_for('org.members'))

    if user_org.role == 'admin' and admin_count <= 1:
        flash('Every organization must have at least 1 admin. Assign admin permissions to another user and try again.')
        return redirect(url_for('org.members'))

    db.session.delete(user_org)
    db.session.commit()
    flash('Member removed from the organization successfully.')
    return redirect(url_for('org.members'))

@bp.route('/change-role/<int:user_id>', methods=['POST'])
@login_required
@require_org_permission('admin')
def change_role(user_id):
    user_org = UserOrganization.query.filter_by(
        user_id=user_id,
        organization_id=g.current_organization.id
    ).first()

    if not user_org:
        flash('Member not found in the organization.')
        return redirect(url_for('org.members'))

    new_role = request.form.get('role')
    if new_role not in ['admin', 'member']:
        flash('Invalid role.')
        return redirect(url_for('org.members'))

    # Count the number of admins in the organization
    admin_count = UserOrganization.query.filter_by(
        organization_id=g.current_organization.id,
        role='admin'
    ).count()

    if user_org.role == 'admin' and new_role == 'member' and admin_count <= 1:
        flash('You cannot change the role of the last admin.')
        return redirect(url_for('org.members'))

    user_org.role = new_role
    db.session.commit()
    flash('Member role updated.')
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
