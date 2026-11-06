"""TC-MR-01 (HAP-F-041, F-044) and TC-MR-02 (HAP-F-042, F-043), plus HAP-SR-006 at-rest encryption."""
from app.services.records.models import ConsultationVersion, PrescriptionItem
from tests.helpers_booking import booked_visit

CONSULT = {"symptoms": "Fever, headache", "vitals": {"bp": "120/80", "pulse": 88, "tempC": 38.4, "weightKg": 61},
           "diagnosis": "Viral fever", "notes": "Fluids, rest; review in 5 days"}
ITEMS = [{"medicine": "Paracetamol 650 mg", "dosage": "1 tablet", "frequency": "3 times a day", "durationDays": 5,
          "instructions": "After food"},
         {"medicine": "Cetirizine 10 mg", "dosage": "1 tablet", "frequency": "At night", "durationDays": 3}]


def checked_in_visit(client, make_user):
    v = booked_visit(client, make_user)
    _, rec_h = make_user("RECEPTIONIST")
    r = client.patch(f"/api/v1/appointments/{v['appointment']['id']}/status", headers=rec_h, json={"status": "CHECKED_IN"})
    assert r.status_code == 200
    v["reception_h"] = rec_h
    return v


def test_tc_mr_01_consultation_completes_appointment_and_edit_creates_version(client, make_user):
    v = checked_in_visit(client, make_user)
    aid = v["appointment"]["id"]
    r = client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT)
    assert r.status_code == 201 and r.json()["version"] == 1 and r.json()["appointmentStatus"] == "COMPLETED"
    cid = r.json()["consultationId"]
    assert client.get(f"/api/v1/appointments/{aid}", headers=v["doctor_h"]).json()["status"] == "COMPLETED"
    r = client.put(f"/api/v1/consultations/{cid}", headers=v["doctor_h"],
                   json={**CONSULT, "diagnosis": "Dengue fever", "changeReason": "Lab report positive"})
    assert r.status_code == 200 and r.json()["version"] == 2
    r = client.get(f"/api/v1/consultations/{cid}?include=versions", headers=v["doctor_h"]).json()
    assert r["current"]["diagnosis"] == "Dengue fever" and r["current"]["changeReason"] == "Lab report positive"
    assert r["previousVersions"][0]["version"] == 1 and r["previousVersions"][0]["diagnosis"] == "Viral fever"
    assert r["previousVersions"][0]["authorId"] and r["previousVersions"][0]["createdAt"]
    assert client.delete(f"/api/v1/consultations/{cid}", headers=v["doctor_h"]).status_code == 405
    chart = client.get(f"/api/v1/patients/{v['patient']['id']}/records", headers=v["doctor_h"]).json()
    assert chart["visits"][0]["diagnosis"] == "Dengue fever" and chart["visits"][0]["version"] == 2


def test_tc_mr_01_consultation_requires_check_in_and_valid_vitals(client, make_user):
    v = booked_visit(client, make_user)
    aid = v["appointment"]["id"]
    r = client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT)
    assert r.status_code == 409 and r.json()["error"]["code"] == "APPOINTMENT_NOT_CHECKED_IN"
    bad = {**CONSULT, "vitals": {"pulse": 400}}
    assert client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=bad).status_code == 422
    assert client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"],
                       json={**CONSULT, "vitals": {"bp": "high"}}).status_code == 422


def test_only_treating_doctor_writes_and_edits(client, make_user):
    from tests.helpers_people import make_doctor
    v = checked_in_visit(client, make_user)
    other_h, _ = make_doctor(client, make_user, v["admin"], name="Dr A Shah")
    aid = v["appointment"]["id"]
    assert client.post(f"/api/v1/appointments/{aid}/consultation", headers=other_h, json=CONSULT).status_code == 403
    cid = client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT).json()["consultationId"]
    assert client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT).status_code == 409
    assert client.put(f"/api/v1/consultations/{cid}", headers=other_h,
                      json={**CONSULT, "changeReason": "mine now"}).status_code == 403
    assert client.put(f"/api/v1/consultations/{cid}", headers=v["doctor_h"], json=CONSULT).status_code == 422  # no reason
    assert client.put("/api/v1/consultations/999", headers=v["doctor_h"], json={**CONSULT, "changeReason": "x y z"}).status_code == 404


def test_tc_mr_02_prescription_pdf_and_patient_read_only(client, make_user):
    v = checked_in_visit(client, make_user)
    aid = v["appointment"]["id"]
    client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT)
    r = client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json={"items": ITEMS})
    assert r.status_code == 201 and len(r.json()["items"]) == 2
    rx = r.json()["prescriptionId"]
    bad = {"items": [{k: val for k, val in ITEMS[0].items() if k != "durationDays"}]}
    r = client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json=bad)
    assert r.status_code == 422 and "durationDays" in r.json()["error"]["message"]
    mine = client.get("/api/v1/patients/me/records", headers=v["patient_h"]).json()
    assert [p["prescriptionId"] for p in mine["prescriptions"]] == [rx]
    assert client.get(f"/api/v1/prescriptions/{rx}", headers=v["patient_h"]).json()["items"][0]["medicine"] == "Paracetamol 650 mg"
    pdf = client.get(f"/api/v1/prescriptions/{rx}/pdf", headers=v["patient_h"])
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf" and pdf.content[:4] == b"%PDF"
    assert client.put(f"/api/v1/prescriptions/{rx}", headers=v["patient_h"], json={"items": ITEMS}).status_code in (403, 405)
    assert client.delete(f"/api/v1/prescriptions/{rx}", headers=v["patient_h"]).status_code in (403, 405)
    cid = mine["visits"][0]["consultationId"]
    patient_view = client.get(f"/api/v1/consultations/{cid}", headers=v["patient_h"]).json()
    assert patient_view["current"]["notes"] is None and patient_view["current"]["diagnosis"] == "Viral fever"
    assert client.put(f"/api/v1/consultations/{cid}", headers=v["patient_h"], json={**CONSULT, "changeReason": "x y z"}).status_code == 403


def test_prescription_rules(client, make_user):
    v = booked_visit(client, make_user)
    aid = v["appointment"]["id"]
    r = client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json={"items": ITEMS})
    assert r.status_code == 409   # still only BOOKED
    assert client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json={"items": []}).status_code == 422
    assert client.get("/api/v1/prescriptions/999", headers=v["patient_h"]).status_code == 404


def test_other_patient_cannot_read_prescription(client, make_user):
    from tests.helpers_people import make_patient
    v = checked_in_visit(client, make_user)
    aid = v["appointment"]["id"]
    rx = client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json={"items": ITEMS}).json()["prescriptionId"]
    _, other_h, _ = make_patient(client, make_user, phone="9000044444")
    assert client.get(f"/api/v1/prescriptions/{rx}", headers=other_h).status_code == 403
    assert client.get(f"/api/v1/prescriptions/{rx}/pdf", headers=other_h).status_code == 403


def test_sensitive_fields_are_ciphertext_in_database(client, make_user, db):
    v = checked_in_visit(client, make_user)
    aid = v["appointment"]["id"]
    client.post(f"/api/v1/appointments/{aid}/consultation", headers=v["doctor_h"], json=CONSULT)
    client.post(f"/api/v1/appointments/{aid}/prescriptions", headers=v["doctor_h"], json={"items": ITEMS})
    row = db.query(ConsultationVersion).first()
    assert row.diagnosis_enc.startswith("v1:") and "Viral" not in row.diagnosis_enc and "Fluids" not in row.notes_enc
    assert all(i.medicine_enc.startswith("v1:") and "Paracetamol" not in i.medicine_enc for i in db.query(PrescriptionItem))
