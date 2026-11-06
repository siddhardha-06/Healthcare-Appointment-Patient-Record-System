from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import crypto, events
from app.core.database import get_db
from app.core.errors import conflict, forbidden, not_found
from app.core.roles import Role
from app.core.security import client_ip, require_roles
from app.services.appointments.models import Status
from app.services.appointments.service import get_appointment
from app.services.doctors.models import Doctor
from app.services.patients.models import Patient
from app.services.records.access import authorize_chart, current_doctor
from app.services.records.models import Prescription, PrescriptionItem
from app.services.records.pdf import prescription_pdf
from app.services.records.schemas_clinical import PrescriptionIn, PrescriptionOut

router = APIRouter(tags=["records"])


def _out(db: Session, rx: Prescription) -> dict:
    patient = db.get(Patient, rx.patient_id)
    doctor = db.get(Doctor, rx.doctor_id)
    items = [{"medicine": crypto.decrypt(i.medicine_enc), "dosage": i.dosage, "frequency": i.frequency,
              "duration_days": i.duration_days, "instructions": i.instructions} for i in rx.items]
    return {"prescription_id": rx.id, "appointment_id": rx.appointment_id, "date": rx.issued_at, "doctor": doctor.name,
            "patient_mrn": patient.mrn, "patient_name": patient.full_name, "items": items, "version": rx.version,
            "pdf_url": f"/api/v1/prescriptions/{rx.id}/pdf"}


@router.post("/appointments/{appointment_id}/prescriptions", response_model=PrescriptionOut, status_code=201)
def issue_prescription(appointment_id: int, data: PrescriptionIn, request: Request,
                       user=Depends(require_roles(Role.DOCTOR)), db: Session = Depends(get_db)):
    """HAP-F-042"""
    doctor = current_doctor(db, user)
    appt = get_appointment(db, appointment_id)
    if appt.doctor_id != doctor.id:
        raise forbidden("This appointment belongs to another doctor.")
    if appt.status not in (Status.CHECKED_IN, Status.COMPLETED):
        raise conflict("APPOINTMENT_NOT_CHECKED_IN", "Prescriptions can only be issued for a checked-in or completed visit.")
    rx = Prescription(appointment_id=appt.id, patient_id=appt.patient_id, doctor_id=doctor.id)
    db.add(rx)
    db.flush()
    for it in data.items:
        db.add(PrescriptionItem(prescription_id=rx.id, medicine_enc=crypto.encrypt(it.medicine), dosage=it.dosage,
                                frequency=it.frequency, duration_days=it.duration_days, instructions=it.instructions))
    db.flush()
    db.refresh(rx)
    events.audit(db, user, "WRITE", "prescription", rx.id, client_ip(request), f"{len(data.items)} items")
    events.publish("prescription.issued", db=db, prescription=rx)
    db.commit()
    return _out(db, rx)


def _load_for_reader(db: Session, prescription_id: int, user, request: Request) -> Prescription:
    rx = db.get(Prescription, prescription_id)
    if rx is None:
        raise not_found("Prescription")
    authorize_chart(db, user, rx.patient_id, request)
    events.audit(db, user, "READ", "prescription", rx.id, client_ip(request))
    db.commit()
    return rx


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionOut)
def get_prescription(prescription_id: int, request: Request, user=Depends(require_roles(Role.DOCTOR, Role.PATIENT)),
                     db: Session = Depends(get_db)):
    """HAP-F-043: patients read their own prescriptions; doctors need a care relationship."""
    return _out(db, _load_for_reader(db, prescription_id, user, request))


@router.get("/prescriptions/{prescription_id}/pdf")
def prescription_as_pdf(prescription_id: int, request: Request, user=Depends(require_roles(Role.DOCTOR, Role.PATIENT)),
                        db: Session = Depends(get_db)):
    rx = _load_for_reader(db, prescription_id, user, request)
    return Response(prescription_pdf(_out(db, rx)), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="rx-{rx.id}.pdf"'})
