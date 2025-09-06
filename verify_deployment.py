#!/usr/bin/env python3
"""
Verification script for the unified backend deployment
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://chat-cv1i.onrender.com"

def test_endpoint(method, path, data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        status_ok = response.status_code == expected_status or response.status_code == 404
        
        return {
            "path": path,
            "method": method,
            "status_code": response.status_code,
            "success": status_ok,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:100]
        }
        
    except Exception as e:
        return {
            "path": path, 
            "method": method,
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

def main():
    """Run all verification tests"""
    print(f"🔍 Verifying Unified Backend Deployment")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test cases
    tests = [
        # Legacy compatibility tests
        ("GET", "/", None, 200),
        ("GET", "/verificar", None, 200),
        ("GET", "/canales", None, 200),
        
        # New API endpoints
        ("GET", "/api/auth/status", None, 200),
        ("GET", "/api/channels/", None, 200),
        ("GET", "/api/personnel/cuadrillas/", None, 200),
        ("GET", "/api/personnel/obreros/", None, 200),
        ("GET", "/api/reports/personal/resumen", None, 200),
        ("GET", "/api/reports/chat/resumen", None, 200),
        ("GET", "/api/reports/exportar/cuadrillas", None, 200),
        
        # Test creating personnel (should work with new endpoints)
        ("POST", "/api/personnel/cuadrillas/", {
            "numero_cuadrilla": "TEST001", 
            "actividad": "Test deployment"
        }, 201),
        
        ("POST", "/api/personnel/obreros/", {
            "nombre": "Test",
            "apellido": "User", 
            "cedula": "12345678"
        }, 201),
    ]
    
    # Execute tests
    results = []
    legacy_count = 0
    new_api_count = 0
    
    for method, path, data, expected_status in tests:
        print(f"Testing {method} {path}...", end=" ")
        
        result = test_endpoint(method, path, data, expected_status)
        results.append(result)
        
        if result["success"]:
            print("✅ PASS")
            if path.startswith("/api/"):
                new_api_count += 1
            else:
                legacy_count += 1
        else:
            print(f"❌ FAIL ({result.get('status_code', 'ERROR')})")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    print(f"✅ Legacy Endpoints: {legacy_count} working")
    print(f"🆕 New API Endpoints: {new_api_count} working")
    
    # Show any failures
    failures = [r for r in results if not r["success"]]
    if failures:
        print("\n❌ FAILED TESTS:")
        for failure in failures:
            print(f"  {failure['method']} {failure['path']} - {failure.get('error', 'Status: ' + str(failure['status_code']))}")
    
    # Final status
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Deployment successful!")
        return 0
    elif legacy_count > 0:
        print(f"\n⚠️  PARTIAL SUCCESS: Legacy compatibility maintained, {total_tests - passed_tests} new features need attention")
        return 1
    else:
        print("\n💥 DEPLOYMENT FAILED: Critical issues detected")
        return 2

if __name__ == "__main__":
    exit(main())