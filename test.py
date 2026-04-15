#!/usr/bin/env python3
"""
Test script for EagleCode Backend API
Run with: python test_backend.py
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def print_section(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_health():
    print_section("1. Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Total Projects: {data.get('total_projects')}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_projects():
    print_section("2. Testing Get Projects API")
    try:
        # Test with limit=1 (latest project only)
        response = requests.get(f"{API_URL}/get-projects?user_id=default&limit=1")
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"   Success: {data.get('success')}")
        print(f"   Projects Count: {data.get('count')}")
        print(f"   Total Projects: {data.get('total', 'N/A')}")
        
        if data.get('projects'):
            project = data['projects'][0]
            print(f"\n   Latest Project:")
            print(f"   - ID: {project.get('id')}")
            print(f"   - Name: {project.get('name')}")
            print(f"   - Type: {project.get('project_type')}")
            print(f"   - Files: {project.get('file_count')}")
            print(f"   - Timestamp: {project.get('timestamp')}")
        
        return data
    except Exception as e:
        print(f"❌ Get projects failed: {e}")
        return None

def test_get_all_projects():
    print_section("3. Testing Get All Projects (limit=100)")
    try:
        response = requests.get(f"{API_URL}/get-projects?user_id=default&limit=100")
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"   Success: {data.get('success')}")
        print(f"   Projects Count: {data.get('count')}")
        print(f"   Total: {data.get('total', 'N/A')}")
        
        if data.get('projects'):
            print(f"\n   All Projects:")
            for i, project in enumerate(data['projects'][:5]):  # Show first 5
                print(f"   {i+1}. {project.get('name')} - {project.get('timestamp')}")
            if len(data['projects']) > 5:
                print(f"   ... and {len(data['projects']) - 5} more")
        
        return data
    except Exception as e:
        print(f"❌ Get all projects failed: {e}")
        return None

def test_get_single_project():
    print_section("4. Testing Get Single Project")
    try:
        # First get a project ID
        list_response = requests.get(f"{API_URL}/get-projects?user_id=default&limit=1")
        if list_response.status_code == 200:
            projects = list_response.json().get('projects', [])
            if projects:
                project_id = projects[0]['id']
                print(f"   Testing with Project ID: {project_id}")
                
                response = requests.get(f"{API_URL}/get-project/{project_id}")
                print(f"✅ Status Code: {response.status_code}")
                data = response.json()
                print(f"   Success: {data.get('success')}")
                
                if data.get('project'):
                    project = data['project']
                    print(f"   Project Name: {project.get('name')}")
                    print(f"   Files Count: {len(data.get('files', {}))}")
                    return True
        print("❌ No projects found to test")
        return False
    except Exception as e:
        print(f"❌ Get single project failed: {e}")
        return False

def test_websocket():
    print_section("5. Testing WebSocket Connection")
    try:
        import websocket
        ws_url = "ws://localhost:8000/ws/build"
        print(f"   Connecting to: {ws_url}")
        
        ws = websocket.create_connection(ws_url, timeout=5)
        print("✅ WebSocket connected successfully")
        
        # Send a test message
        test_message = json.dumps({"prompt": "test"})
        ws.send(test_message)
        print("   Message sent")
        
        # Wait for response (with timeout)
        ws.settimeout(5)
        try:
            response = ws.recv()
            print(f"   Response received: {response[:100]}...")
        except:
            print("   No response received (may be normal)")
        
        ws.close()
        print("✅ WebSocket closed")
        return True
    except ImportError:
        print("⚠️ websocket-client not installed. Run: pip install websocket-client")
        return False
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def test_cors():
    print_section("6. Testing CORS Headers")
    try:
        response = requests.options(f"{API_URL}/get-projects", 
                                    headers={"Origin": "http://localhost:3000"})
        print(f"✅ Status Code: {response.status_code}")
        cors_headers = {
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
        }
        for key, value in cors_headers.items():
            print(f"   {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def main():
    print("\n" + "🦅"*30)
    print("   EAGLECODE BACKEND TEST SUITE")
    print("🦅"*30)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Get Projects (Latest)", test_get_projects() is not None))
    results.append(("Get All Projects", test_get_all_projects() is not None))
    results.append(("Get Single Project", test_get_single_project()))
    results.append(("WebSocket", test_websocket()))
    results.append(("CORS Headers", test_cors()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is ready!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    main()