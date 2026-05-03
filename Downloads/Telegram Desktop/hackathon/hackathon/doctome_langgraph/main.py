from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
import asyncio
from typing import List
from graph import run_verification_workflow
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doctome.api")

app = FastAPI(title="DocTome AI Verification API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "DocTome API is running"}

@app.post("/api/verify")
async def verify_practitioner(
    doctorName: str = Form(...),
    licenseNumber: str = Form(...),
    specialty: str = Form(...),
    country: str = Form(...),
    entityType: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Unified verification endpoint for Doctors, Clinics, and Laboratories.
    """
    logger.info(f"Received verification request for {doctorName} ({entityType})")
    
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    saved_docs = []
    
    try:
        # Save uploaded files
        for file in files:
            file_path = os.path.join(session_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Basic type detection based on filename or order (can be improved)
            doc_type = "document"
            if "diploma" in file.filename.lower() or "diplôme" in file.filename.lower():
                doc_type = "diploma"
            elif "id" in file.filename.lower() or "identit" in file.filename.lower() or "passport" in file.filename.lower():
                doc_type = "id"
            elif "license" in file.filename.lower() or "agrément" in file.filename.lower() or "licence" in file.filename.lower():
                doc_type = "license"
            elif "iso" in file.filename.lower() or "accreditation" in file.filename.lower():
                doc_type = "certification"
                
            saved_docs.append({
                "path": file_path,
                "type": doc_type,
                "original_name": file.filename
            })
            
        logger.info(f"Saved {len(saved_docs)} documents for session {session_id}")
        
        # Run the LangGraph workflow
        # Note: entityType can be 'doctor', 'clinic', or 'lab'
        result_state = await run_verification_workflow(
            practitioner_id=session_id,
            full_name=doctorName,
            specialty=specialty,
            country=country,
            registration_number=licenseNumber,
            documents=saved_docs
        )
        
        # Format the response for the frontend
        # The frontend ResultsDashboard expects: { practitioner: {...}, pipeline: { extraction: {...}, verification: {...}, report: {...} }, errors: [...] }
        
        # Map state fields to frontend-ready structure
        response = {
            "status": "success",
            "practitioner": {
                "name": result_state.get("full_name"),
                "registrationNumber": result_state.get("registration_number"),
                "specialty": result_state.get("specialty"),
                "country": result_state.get("country")
            },
            "pipeline": {
                "extraction": {
                    "totalDocuments": result_state.get("document_count", len(saved_docs)),
                    "averageQuality": result_state.get("document_quality", 0.9),
                    "totalAnomalies": len(result_state.get("doc_anomalies", [])),
                    "documents": result_state.get("extraction_documents_json", [])
                },
                "verification": {
                    "trustScore": result_state.get("final_trust_score", 0),
                    "totalIssues": len(result_state.get("credential_flags", [])),
                    "issues": result_state.get("credential_flags", []),
                    "categoryBreakdown": result_state.get("verification_json_output", {}).get("category_scores", {})
                },
                "report": {
                    "decision": result_state.get("decision", "PENDING"),
                    "reasoning": result_state.get("final_reasoning", ""),
                    "priority": result_state.get("risk_assessment_json_output", {}).get("priority", "MEDIUM"),
                    "requiresHumanReview": result_state.get("decision") == "PENDING_REVIEW",
                    "nextSteps": result_state.get("report_json_output", {}).get("next_steps", [])
                }
            },
            "errors": result_state.get("error_messages", []),
            "logs": result_state.get("processing_log", [])
        }
        
        return response

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
