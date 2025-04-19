#!/usr/bin/env python
"""
Simple test script for the WanderMatch API.
Tests the health endpoint and survey endpoint.
"""
import requests
import json

API_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint returned: {data}")
            return True
        else:
            print(f"❌ Health endpoint returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {str(e)}")
        return False

def test_survey_endpoint():
    """Test the survey endpoint with a sample submission"""
    print("\nTesting survey endpoint...")
    sample_data = {
        "real_name": "Test User",
        "age_group": "25-34",
        "gender": "Not specified",
        "nationality": "Test Nation",
        "travel_budget": "$1000",
        "travel_season": "Summer",
        "interests": "Testing, traveling",
        "travel_style": "Cultural",
        "accommodation_preference": "Mid-range hotel"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/survey", 
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Survey saved successfully: {data.get('filename')}")
                return True
            else:
                print(f"❌ Survey endpoint returned error: {data.get('message')}")
                return False
        else:
            print(f"❌ Survey endpoint returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing survey endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    print("WanderMatch API Test Script")
    print("==========================\n")
    
    health_result = test_health_endpoint()
    survey_result = test_survey_endpoint()
    
    print("\nTest Summary")
    print("===========")
    print(f"Health Endpoint: {'✅ PASSED' if health_result else '❌ FAILED'}")
    print(f"Survey Endpoint: {'✅ PASSED' if survey_result else '❌ FAILED'}")
    
    if health_result and survey_result:
        print("\n✅ All tests passed! The API is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the API server.") 