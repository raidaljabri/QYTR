#!/usr/bin/env python3
"""
Backend API Testing for Arabic Quote Management System
Tests all CRUD operations, company management, and export functionality
"""

import requests
import sys
import json
import os
from datetime import datetime
from io import BytesIO

class QuoteManagementAPITester:
    def __init__(self, base_url="https://awning-quotations.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_quote_id = None
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                print(f"   Status: {response.status_code} ✅")
                try:
                    response_data = response.json() if response.content else {}
                    print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)[:200]}...")
                except:
                    print(f"   Response: Non-JSON content (length: {len(response.content)})")
                self.log_test(name, True)
                return True, response_data if 'response_data' in locals() else {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                print(f"   Status: {response.status_code} ❌")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                    error_msg += f" - {error_detail}"
                except:
                    print(f"   Error: {response.text[:200]}")
                    error_msg += f" - {response.text[:200]}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   Exception: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_company_info(self):
        """Test getting company information"""
        return self.run_test("Get Company Info", "GET", "company", 200)

    def test_update_company_info(self):
        """Test updating company information"""
        company_data = {
            "name_ar": "شركة مثلث الأنظمة المميزة للمقاولات - محدث",
            "name_en": "MUTHALLATH AL-ANZIMAH AL-MUMAYYIZAH CONTRACTING CO. - Updated",
            "description_ar": "تصميم وتصنيع وتوريد وتركيب مظلات الشد الإنشائي والخيام والسواتر",
            "description_en": "Design, Manufacture, Supply & Installation of Structure Tension Awnings, Tents & Canopies",
            "tax_number": "311104439400003",
            "street": "شارع حائل",
            "neighborhood": "حي البغدادية الغربية",
            "country": "السعودية",
            "city": "جدة",
            "commercial_registration": "4030255240",
            "building": "8376",
            "postal_code": "22231",
            "additional_number": "3842",
            "email": "info@tsscoksa.com",
            "phone1": "+966 50 061 2006",
            "phone2": "055 538 9792",
            "phone3": "+966 50 336 5527"
        }
        return self.run_test("Update Company Info", "PUT", "company", 200, company_data)

    def test_create_quote(self):
        """Test creating a new quote"""
        quote_data = {
            "customer": {
                "name": "شركة الاختبار للمقاولات",
                "tax_number": "123456789012345",
                "street": "شارع الملك فهد",
                "neighborhood": "حي العليا",
                "country": "السعودية",
                "city": "الرياض",
                "commercial_registration": "1234567890",
                "building": "123",
                "postal_code": "12345",
                "additional_number": "6789",
                "phone": "+966 50 123 4567"
            },
            "project_description": "تركيب مظلات للمواقف في مجمع تجاري",
            "location": "الرياض - حي العليا",
            "items": [
                {
                    "description": "مظلة شد إنشائي 10x10 متر",
                    "quantity": 2,
                    "unit": "قطعة",
                    "unit_price": 15000.0,
                    "total_price": 30000.0
                },
                {
                    "description": "أعمال التركيب والتشطيب",
                    "quantity": 1,
                    "unit": "مجموعة",
                    "unit_price": 5000.0,
                    "total_price": 5000.0
                }
            ],
            "subtotal": 35000.0,
            "tax_amount": 5250.0,
            "total_amount": 40250.0,
            "notes": "يشمل العرض الضمان لمدة سنتين"
        }
        
        success, response = self.run_test("Create Quote", "POST", "quotes", 200, quote_data)
        if success and 'id' in response:
            self.created_quote_id = response['id']
            print(f"   Created quote ID: {self.created_quote_id}")
        return success, response

    def test_get_quotes_list(self):
        """Test getting list of quotes"""
        return self.run_test("Get Quotes List", "GET", "quotes", 200)

    def test_get_single_quote(self):
        """Test getting a single quote by ID"""
        if not self.created_quote_id:
            self.log_test("Get Single Quote", False, "No quote ID available")
            return False, {}
        
        return self.run_test("Get Single Quote", "GET", f"quotes/{self.created_quote_id}", 200)

    def test_update_quote(self):
        """Test updating an existing quote"""
        if not self.created_quote_id:
            self.log_test("Update Quote", False, "No quote ID available")
            return False, {}
        
        update_data = {
            "project_description": "تركيب مظلات للمواقف في مجمع تجاري - محدث",
            "notes": "يشمل العرض الضمان لمدة سنتين "
        }
        
        return self.run_test("Update Quote", "PUT", f"quotes/{self.created_quote_id}", 200, update_data)

    def test_export_quote_pdf(self):
        """Test exporting quote as PDF"""
        if not self.created_quote_id:
            self.log_test("Export Quote PDF", False, "No quote ID available")
            return False, {}
        
        url = f"{self.api_url}/quotes/{self.created_quote_id}/export/pdf"
        print(f"\n🔍 Testing Export Quote PDF...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            success = response.status_code == 200 and response.headers.get('content-type') == 'application/pdf'
            
            if success:
                print(f"   Status: {response.status_code} ✅")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                self.log_test("Export Quote PDF", True)
                return True, {}
            else:
                error_msg = f"Expected PDF content, got {response.status_code} with content-type: {response.headers.get('content-type')}"
                print(f"   Status: {response.status_code} ❌")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                self.log_test("Export Quote PDF", False, error_msg)
                return False, {}
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   Exception: {error_msg}")
            self.log_test("Export Quote PDF", False, error_msg)
            return False, {}

    def test_export_quote_excel(self):
        """Test exporting quote as Excel"""
        if not self.created_quote_id:
            self.log_test("Export Quote Excel", False, "No quote ID available")
            return False, {}
        
        url = f"{self.api_url}/quotes/{self.created_quote_id}/export/excel"
        print(f"\n🔍 Testing Export Quote Excel...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            expected_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            success = response.status_code == 200 and expected_content_type in response.headers.get('content-type', '')
            
            if success:
                print(f"   Status: {response.status_code} ✅")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                self.log_test("Export Quote Excel", True)
                return True, {}
            else:
                error_msg = f"Expected Excel content, got {response.status_code} with content-type: {response.headers.get('content-type')}"
                print(f"   Status: {response.status_code} ❌")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                self.log_test("Export Quote Excel", False, error_msg)
                return False, {}
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"   Exception: {error_msg}")
            self.log_test("Export Quote Excel", False, error_msg)
            return False, {}

    def test_delete_quote(self):
        """Test deleting a quote"""
        if not self.created_quote_id:
            self.log_test("Delete Quote", False, "No quote ID available")
            return False, {}
        
        return self.run_test("Delete Quote", "DELETE", f"quotes/{self.created_quote_id}", 200)

    def test_get_nonexistent_quote(self):
        """Test getting a non-existent quote (should return 404)"""
        fake_id = "nonexistent-quote-id-12345"
        return self.run_test("Get Non-existent Quote", "GET", f"quotes/{fake_id}", 404)

    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 60)
        print("🚀 Starting Arabic Quote Management System API Tests")
        print("=" * 60)
        
        # Test API connectivity
        self.test_api_root()
        
        # Test company management
        self.test_get_company_info()
        self.test_update_company_info()
        
        # Test quote CRUD operations
        self.test_create_quote()
        self.test_get_quotes_list()
        self.test_get_single_quote()
        self.test_update_quote()
        
        # Test export functionality
        self.test_export_quote_pdf()
        self.test_export_quote_excel()
        
        # Test error handling
        self.test_get_nonexistent_quote()
        
        # Clean up - delete the test quote
        self.test_delete_quote()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
            return 1

def main():
    """Main function to run the tests"""
    tester = QuoteManagementAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())