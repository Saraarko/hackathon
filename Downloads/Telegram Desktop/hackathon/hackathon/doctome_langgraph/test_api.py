import requests
import os

API_URL = "http://localhost:8000/api/verify"

def test_verify():
    # Use an existing test document
    doc_path = "data/DOCTOR_DIPLOMA_FR.pdf"
    
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found")
        return

    print(f"Sending {doc_path} to API...")
    
    files = [
        ('files', open(doc_path, 'rb'))
    ]
    
    data = {
        'doctorName': 'Dr. Ahmed Ben Ali',
        'licenseNumber': '12345ABC',
        'specialty': 'Cardiology',
        'country': 'Algeria',
        'entityType': 'doctor'
    }
    
    try:
        response = requests.post(API_URL, data=data, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("\nVERIFICATION RESULT:")
            print(f"Name: {result['practitioner']['name']}")
            print(f"Trust Score: {result['pipeline']['verification']['trustScore']}/100")
            print(f"Decision: {result['pipeline']['report']['decision']}")
            print(f"Reasoning: {result['pipeline']['report']['reasoning']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_verify()
