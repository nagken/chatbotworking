#!/usr/bin/env python3
"""
Test feedback submission specifically
"""

import requests
import json


def test_feedback_submission():
    """Test the feedback submission endpoint"""
    base_url = "http://127.0.0.1:8080"
    
    print("🧪 Testing Feedback Submission")
    print("=" * 40)
    
    # Step 1: Login first
    print("\n1. Logging in...")
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = login_response.json()
    session_token = login_data.get('session_token')
    print(f"✅ Login successful")
    
    # Step 2: Test feedback submission
    print("\n2. Testing feedback submission...")
    
    headers = {"Authorization": f"Bearer {session_token}"}
    
    # Test with a mock message ID
    message_id = "12345678-1234-5678-9012-123456789012"  # Valid UUID format
    
    feedback_data = {
        "is_positive": False,  # Thumbs down
        "feedback_comment": "This is a test feedback comment from the test script"
    }
    
    feedback_response = requests.post(
        f"{base_url}/api/feedback/messages/{message_id}/feedback",
        json=feedback_data,
        headers=headers
    )
    
    print(f"Feedback Status: {feedback_response.status_code}")
    print(f"Feedback Response: {feedback_response.text}")
    
    if feedback_response.status_code == 200:
        result = feedback_response.json()
        print(f"✅ Feedback submitted successfully!")
        print(f"   Message: {result.get('message', 'No message')}")
        print(f"   Feedback ID: {result.get('feedback_id', 'No ID')}")
    else:
        print(f"❌ Feedback submission failed")
        try:
            error_detail = feedback_response.json()
            print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
        except:
            print(f"   Raw error: {feedback_response.text}")
    
    print("\n" + "=" * 40)
    print("🎯 Feedback test completed!")


if __name__ == "__main__":
    test_feedback_submission()
