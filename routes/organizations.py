from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.organization import Organization, BankerOrganization
from schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse, BankerOrganizationResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=list[BankerOrganizationResponse])
def get_my_organizations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orgs = db.query(BankerOrganization).filter(BankerOrganization.user_id == current_user.id).all()
    return orgs

@router.post("", response_model=OrganizationResponse)
def create_organization(org_data: OrganizationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = Organization(
        name=org_data.name,
        organization_type=org_data.organization_type,
        branch_name=org_data.branch_name,
        branch_code=org_data.branch_code,
        city=org_data.city,
        state=org_data.state,
        office_contact=org_data.office_contact
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Link to user
    banker_org = BankerOrganization(
        user_id=current_user.id,
        organization_id=org.id,
        is_primary=True
    )
    db.add(banker_org)
    db.commit()

    return org

@router.patch("/{org_id}", response_model=OrganizationResponse)
def update_organization(org_id: int, org_data: OrganizationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify access
    banker_org = db.query(BankerOrganization).filter(
        BankerOrganization.user_id == current_user.id,
        BankerOrganization.organization_id == org_id
    ).first()
    
    if not banker_org:
        raise HTTPException(status_code=403, detail="Not authorized to edit this organization")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org_data.name is not None:
        org.name = org_data.name
    if org_data.organization_type is not None:
        org.organization_type = org_data.organization_type
    if org_data.branch_name is not None:
        org.branch_name = org_data.branch_name
    if org_data.branch_code is not None:
        org.branch_code = org_data.branch_code
    if org_data.city is not None:
        org.city = org_data.city
    if org_data.state is not None:
        org.state = org_data.state
    if org_data.office_contact is not None:
        org.office_contact = org_data.office_contact

    db.commit()
    db.refresh(org)
    return org
