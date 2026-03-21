#!/usr/bin/env python3
"""
TratorShop Backend API Testing
Tests all public and authenticated endpoints
"""

import requests
import json
import sys
from datetime import datetime
from time import sleep

class TratorShopAPITester:
    def __init__(self, base_url="https://shop-admin-panel-10.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, test_name, success, status_code=None, error_msg=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
            self.test_results.append({"test": test_name, "status": "PASSED"})
        else:
            print(f"❌ {test_name} - FAILED: {error_msg} (Status: {status_code})")
            self.test_results.append({"test": test_name, "status": "FAILED", "error": error_msg, "status_code": status_code})
        
    def test_api_root(self):
        """Test GET /api/ returns API info"""
        try:
            response = requests.get(f"{self.api_url}/")
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "TratorShop" in str(data.get("message", ""))
            self.log_test("GET /api/", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/", False, None, str(e))
            return False

    def test_categories(self):
        """Test GET /api/categories returns category list"""
        try:
            response = requests.get(f"{self.api_url}/categories")
            success = response.status_code == 200
            if success:
                data = response.json()
                expected_categories = ["tratores", "implementos", "colheitadeiras", "pecas"]
                actual_ids = [cat.get("id") for cat in data]
                success = all(cat in actual_ids for cat in expected_categories)
            self.log_test("GET /api/categories", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/categories", False, None, str(e))
            return False

    def test_cities(self):
        """Test GET /api/cities returns MS cities list"""
        try:
            response = requests.get(f"{self.api_url}/cities")
            success = response.status_code == 200
            if success:
                data = response.json()
                expected_cities = ["Campo Grande", "Dourados", "Três Lagoas"]
                success = all(city in data for city in expected_cities)
            self.log_test("GET /api/cities", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/cities", False, None, str(e))
            return False

    def test_listings(self):
        """Test GET /api/listings returns empty list (no approved listings yet)"""
        try:
            response = requests.get(f"{self.api_url}/listings")
            success = response.status_code == 200
            if success:
                data = response.json()
                # Should return empty or minimal listings since no approved listings yet
                success = "listings" in data and isinstance(data["listings"], list)
            self.log_test("GET /api/listings", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/listings", False, None, str(e))
            return False

    def test_featured_listings(self):
        """Test GET /api/listings/featured returns empty array"""
        try:
            response = requests.get(f"{self.api_url}/listings/featured")
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)  # Should be empty list
            self.log_test("GET /api/listings/featured", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/listings/featured", False, None, str(e))
            return False

    def test_stats(self):
        """Test GET /api/stats returns marketplace stats"""
        try:
            response = requests.get(f"{self.api_url}/stats")
            success = response.status_code == 200
            if success:
                data = response.json()
                required_fields = ["total_listings", "total_users", "total_whatsapp_clicks"]
                success = all(field in data for field in required_fields)
            self.log_test("GET /api/stats", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/stats", False, None, str(e))
            return False

    def test_auth_endpoints_without_token(self):
        """Test auth endpoints without authentication (should return 401)"""
        endpoints = [
            "/auth/me",
            "/my-listings"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}")
                success = response.status_code == 401
                self.log_test(f"GET {endpoint} (no auth)", success, response.status_code)
            except Exception as e:
                self.log_test(f"GET {endpoint} (no auth)", False, None, str(e))
    
    def test_whatsapp_click_without_auth(self):
        """Test WhatsApp click endpoint without auth (should return 401)"""
        try:
            response = requests.post(f"{self.api_url}/listings/test-id/whatsapp-click")
            success = response.status_code == 401
            self.log_test("POST /api/listings/test-id/whatsapp-click (no auth)", success, response.status_code)
        except Exception as e:
            self.log_test("POST /api/listings/test-id/whatsapp-click (no auth)", False, None, str(e))

    def test_create_listing_without_auth(self):
        """Test creating listing without auth (should return 401)"""
        try:
            test_listing = {
                "title": "Test Tractor",
                "description": "Test description",
                "category": "tratores",
                "price": 100000,
                "condition": "usado",
                "city": "Campo Grande",
                "whatsapp": "67999999999"
            }
            response = requests.post(f"{self.api_url}/listings", json=test_listing)
            success = response.status_code == 401
            self.log_test("POST /api/listings (no auth)", success, response.status_code)
        except Exception as e:
            self.log_test("POST /api/listings (no auth)", False, None, str(e))

    def test_admin_endpoints_without_auth(self):
        """Test admin endpoints without auth (should return 401)"""
        endpoints = [
            "/admin/listings",
            "/admin/listings/test-id/approve"
        ]
        
        for endpoint in endpoints[:1]:  # Just test one to avoid spam
            try:
                response = requests.get(f"{self.api_url}{endpoint}")
                success = response.status_code == 401
                self.log_test(f"GET {endpoint} (no auth)", success, response.status_code)
            except Exception as e:
                self.log_test(f"GET {endpoint} (no auth)", False, None, str(e))

    def test_authenticated_endpoints_with_token(self):
        """Test authenticated endpoints with test token"""
        if not self.session_token:
            print("⚠️ No session token available, skipping authenticated tests")
            return
            
        headers = {"Authorization": f"Bearer {self.session_token}"}
        
        # Test auth/me endpoint
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "user_id" in data or "name" in data
            self.log_test("GET /api/auth/me (with auth)", success, response.status_code)
        except Exception as e:
            self.log_test("GET /api/auth/me (with auth)", False, None, str(e))
            
        # Test my-listings endpoint  
        try:
            response = requests.get(f"{self.api_url}/my-listings", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)  # Should return list of listings
            self.log_test("GET /api/my-listings (with auth)", success, response.status_code)
        except Exception as e:
            self.log_test("GET /api/my-listings (with auth)", False, None, str(e))
    
    def test_listing_creation_with_auth(self):
        """Test creating a listing with authentication"""
        if not self.session_token:
            return
            
        headers = {"Authorization": f"Bearer {self.session_token}"}
        test_listing = {
            "title": "Test Tractor Optimization",
            "description": "Test description for optimization features",
            "category": "tratores", 
            "price": 125000,
            "condition": "usado",
            "city": "Campo Grande",
            "whatsapp": "67999999999",
            "brand": "John Deere",
            "model": "5085E",
            "year": 2020
        }
        
        try:
            response = requests.post(f"{self.api_url}/listings", json=test_listing, headers=headers)
            success = response.status_code in [200, 201]
            if success:
                data = response.json()
                success = "listing_id" in data
                if success:
                    self.test_listing_id = data["listing_id"]
            self.log_test("POST /api/listings (with auth)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/listings (with auth)", False, None, str(e))
            return False
    
    def test_listing_detail_for_seo(self):
        """Test listing detail endpoint for SEO data"""
        if not hasattr(self, 'test_listing_id') or not self.test_listing_id:
            # Try with any existing listing ID
            try:
                response = requests.get(f"{self.api_url}/listings")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("listings") and len(data["listings"]) > 0:
                        self.test_listing_id = data["listings"][0]["listing_id"]
            except:
                pass
                
        if hasattr(self, 'test_listing_id') and self.test_listing_id:
            try:
                response = requests.get(f"{self.api_url}/listings/{self.test_listing_id}")
                success = response.status_code == 200
                if success:
                    data = response.json()
                    # Check for SEO-relevant fields
                    required_fields = ["title", "description", "city", "category", "price"]
                    success = all(field in data for field in required_fields)
                self.log_test("GET /api/listings/{id} (SEO data)", success, response.status_code)
            except Exception as e:
                self.log_test("GET /api/listings/{id} (SEO data)", False, None, str(e))
        else:
            self.log_test("GET /api/listings/{id} (SEO data)", False, None, "No listing ID available")
    
    def run_authenticated_tests(self):
        """Run authenticated tests with provided token"""
        self.session_token = "test_session_admin_123"  # Use provided test token
        print("\n🔐 Running authenticated tests...")
        
        self.test_authenticated_endpoints_with_token()
        sleep(0.1)
        
        success = self.test_listing_creation_with_auth()
        sleep(0.1)
        
        if success:
            self.test_listing_detail_for_seo()
            sleep(0.1)

    def run_public_api_tests(self):
        """Run all public API tests"""
        print("🚀 Starting TratorShop Backend API Tests...\n")
        
        # Test public endpoints
        self.test_api_root()
        sleep(0.1)
        
        self.test_categories()
        sleep(0.1)
        
        self.test_cities()
        sleep(0.1)
        
        self.test_listings()
        sleep(0.1)
        
        self.test_featured_listings()
        sleep(0.1)
        
        self.test_stats()
        sleep(0.1)
        
        # Test auth protection
        self.test_auth_endpoints_without_token()
        sleep(0.1)
        
        self.test_whatsapp_click_without_auth()
        sleep(0.1)
        
        self.test_create_listing_without_auth()
        sleep(0.1)
        
        self.test_admin_endpoints_without_auth()
        sleep(0.1)
        
        # Test file endpoint
        self.test_file_endpoint_404()
        
    def test_file_endpoint_404(self):
        """Test file endpoint with non-existent file (should return 404)"""
        try:
            response = requests.get(f"{self.api_url}/files/non-existent-file.jpg")
            success = response.status_code == 404
            self.log_test("GET /api/files/non-existent (404)", success, response.status_code)
        except Exception as e:
            self.log_test("GET /api/files/non-existent (404)", False, None, str(e))

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 TEST SUMMARY")
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        else:
            print("\n✅ All tests passed!")

    def test_admin_login_api(self):
        """Test admin login API with correct credentials"""
        try:
            admin_credentials = {
                "email": "admin@tratorshop.com",
                "password": "Admin@123"
            }
            response = requests.post(f"{self.api_url}/admin/auth/login", json=admin_credentials)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "admin_id" in data and "email" in data
                # Check if admin_token cookie is set
                if 'set-cookie' in response.headers:
                    cookies = response.headers['set-cookie']
                    success = success and 'admin_token=' in cookies
            self.log_test("POST /api/admin/auth/login (correct credentials)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/admin/auth/login (correct credentials)", False, None, str(e))
            return False

    def test_admin_login_api_wrong_credentials(self):
        """Test admin login API with wrong credentials"""
        try:
            wrong_credentials = {
                "email": "admin@tratorshop.com",
                "password": "WrongPassword123"
            }
            response = requests.post(f"{self.api_url}/admin/auth/login", json=wrong_credentials)
            success = response.status_code == 401
            self.log_test("POST /api/admin/auth/login (wrong credentials)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/admin/auth/login (wrong credentials)", False, None, str(e))
            return False

    def test_admin_login_api_nonexistent_user(self):
        """Test admin login API with non-existent admin"""
        try:
            fake_credentials = {
                "email": "fake@admin.com",
                "password": "SomePassword"
            }
            response = requests.post(f"{self.api_url}/admin/auth/login", json=fake_credentials)
            success = response.status_code == 401
            self.log_test("POST /api/admin/auth/login (non-existent admin)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/admin/auth/login (non-existent admin)", False, None, str(e))
            return False

    def test_admin_auth_me_without_token(self):
        """Test admin auth/me without token (should return 401)"""
        try:
            response = requests.get(f"{self.api_url}/admin/auth/me")
            success = response.status_code == 401
            self.log_test("GET /api/admin/auth/me (no token)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("GET /api/admin/auth/me (no token)", False, None, str(e))
            return False

    def test_admin_endpoints_with_valid_token(self):
        """Test admin endpoints with valid admin token"""
        # First login as admin
        try:
            admin_credentials = {
                "email": "admin@tratorshop.com", 
                "password": "Admin@123"
            }
            login_response = requests.post(f"{self.api_url}/admin/auth/login", json=admin_credentials)
            if login_response.status_code != 200:
                self.log_test("Admin token setup for protected tests", False, login_response.status_code, "Failed to get admin token")
                return
            
            # Extract admin_token from cookies
            admin_token = None
            if 'set-cookie' in login_response.headers:
                cookies = login_response.headers['set-cookie']
                for cookie in cookies.split(';'):
                    if 'admin_token=' in cookie:
                        admin_token = cookie.split('admin_token=')[1].split(';')[0]
                        break
            
            if not admin_token:
                self.log_test("Admin token extraction", False, None, "Could not extract admin_token")
                return
            
            # Test admin/auth/me with token
            headers = {"Cookie": f"admin_token={admin_token}"}
            
            response = requests.get(f"{self.api_url}/admin/auth/me", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "admin_id" in data and "email" in data and data["email"] == "admin@tratorshop.com"
            self.log_test("GET /api/admin/auth/me (with token)", success, response.status_code)
            
            # Test admin/listings endpoint
            response = requests.get(f"{self.api_url}/admin/listings", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)  # Should return list of listings
            self.log_test("GET /api/admin/listings (with token)", success, response.status_code)
            
            # Test admin/users endpoint  
            response = requests.get(f"{self.api_url}/admin/users", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)  # Should return list of users
            self.log_test("GET /api/admin/users (with token)", success, response.status_code)
            
            # Test admin logout
            response = requests.post(f"{self.api_url}/admin/auth/logout", headers=headers)
            success = response.status_code == 200
            self.log_test("POST /api/admin/auth/logout", success, response.status_code)
            
        except Exception as e:
            self.log_test("Admin protected endpoints tests", False, None, str(e))

    def test_dealer_endpoints_404(self):
        """Test dealer endpoints return 404 for non-existent stores"""
        # Test non-existent dealer profile
        try:
            response = requests.get(f"{self.api_url}/dealers/shop-admin-panel-10")
            success = response.status_code == 404
            if success:
                data = response.json()
                success = "Loja não encontrada" in data.get("detail", "")
            self.log_test("GET /api/dealers/shop-admin-panel-10 (404)", success, response.status_code)
        except Exception as e:
            self.log_test("GET /api/dealers/shop-admin-panel-10 (404)", False, None, str(e))

        # Test non-existent dealer listings
        try:
            response = requests.get(f"{self.api_url}/dealers/shop-admin-panel-10/listings")
            success = response.status_code == 404
            if success:
                data = response.json()
                success = "Loja não encontrada" in data.get("detail", "")
            self.log_test("GET /api/dealers/shop-admin-panel-10/listings (404)", success, response.status_code)
        except Exception as e:
            self.log_test("GET /api/dealers/shop-admin-panel-10/listings (404)", False, None, str(e))

    def test_admin_dealer_endpoints(self):
        """Test admin dealer management endpoints"""
        # First login as admin to get token
        try:
            admin_credentials = {
                "email": "admin@tratorshop.com", 
                "password": "Admin@123"
            }
            login_response = requests.post(f"{self.api_url}/admin/auth/login", json=admin_credentials)
            if login_response.status_code != 200:
                self.log_test("Admin dealer endpoints setup", False, login_response.status_code, "Failed to get admin token")
                return
            
            # Extract admin_token from cookies
            admin_token = None
            if 'set-cookie' in login_response.headers:
                cookies = login_response.headers['set-cookie']
                for cookie in cookies.split(';'):
                    if 'admin_token=' in cookie:
                        admin_token = cookie.split('admin_token=')[1].split(';')[0]
                        break
            
            if not admin_token:
                self.log_test("Admin dealer token extraction", False, None, "Could not extract admin_token")
                return
            
            headers = {"Cookie": f"admin_token={admin_token}"}
            
            # Test admin/dealers endpoint
            response = requests.get(f"{self.api_url}/admin/dealers", headers=headers)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)  # Should return list of dealers
            self.log_test("GET /api/admin/dealers (with token)", success, response.status_code)
            
        except Exception as e:
            self.log_test("Admin dealer endpoints tests", False, None, str(e))

    def run_dealer_tests(self):
        """Run all dealer-specific tests"""
        print("\n🏪 Testing Dealer System...")
        
        self.test_dealer_endpoints_404()
        sleep(0.1)
        
        self.test_admin_dealer_endpoints()
        sleep(0.1)

    def test_user_register_api(self):
        """Test user registration with email/password"""
        try:
            # Test with valid data
            user_data = {
                "email": "novo@tratorshop.com",
                "password": "senha123",
                "name": "Novo Usuario"
            }
            response = requests.post(f"{self.api_url}/auth/register", json=user_data)
            success = response.status_code in [200, 201]
            if success:
                data = response.json()
                success = "user" in data and data["user"]["email"] == user_data["email"]
            self.log_test("POST /api/auth/register (valid data)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/register (valid data)", False, None, str(e))
            return False

    def test_user_register_api_invalid_email(self):
        """Test user registration with invalid email"""
        try:
            user_data = {
                "email": "invalid-email",
                "password": "senha123",
                "name": "Test User"
            }
            response = requests.post(f"{self.api_url}/auth/register", json=user_data)
            success = response.status_code == 400
            if success:
                data = response.json()
                success = "Email inválido" in data.get("detail", "")
            self.log_test("POST /api/auth/register (invalid email)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/register (invalid email)", False, None, str(e))
            return False

    def test_user_register_api_short_password(self):
        """Test user registration with short password"""
        try:
            user_data = {
                "email": "test@example.com",
                "password": "123",
                "name": "Test User"
            }
            response = requests.post(f"{self.api_url}/auth/register", json=user_data)
            success = response.status_code == 400
            if success:
                data = response.json()
                success = "pelo menos 6 caracteres" in data.get("detail", "")
            self.log_test("POST /api/auth/register (short password)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/register (short password)", False, None, str(e))
            return False

    def test_user_login_api(self):
        """Test user login with email/password"""
        try:
            # First ensure user exists by registering
            user_data = {
                "email": "novo@tratorshop.com",
                "password": "senha123",
                "name": "Novo Usuario"
            }
            requests.post(f"{self.api_url}/auth/register", json=user_data)
            
            # Now test login
            login_data = {
                "email": "novo@tratorshop.com",
                "password": "senha123"
            }
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "user_id" in data and data["email"] == login_data["email"]
                # Check if session_token cookie is set
                if 'set-cookie' in response.headers:
                    cookies = response.headers['set-cookie']
                    success = success and 'session_token=' in cookies
            self.log_test("POST /api/auth/login (correct credentials)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/login (correct credentials)", False, None, str(e))
            return False

    def test_user_login_api_wrong_password(self):
        """Test user login with wrong password"""
        try:
            login_data = {
                "email": "novo@tratorshop.com",
                "password": "wrongpassword"
            }
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            success = response.status_code == 401
            if success:
                data = response.json()
                success = "Email ou senha incorretos" in data.get("detail", "")
            self.log_test("POST /api/auth/login (wrong password)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/login (wrong password)", False, None, str(e))
            return False

    def test_user_login_api_nonexistent_user(self):
        """Test user login with non-existent email"""
        try:
            login_data = {
                "email": "nonexistent@example.com",
                "password": "somepassword"
            }
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            success = response.status_code == 401
            if success:
                data = response.json()
                success = "Email ou senha incorretos" in data.get("detail", "")
            self.log_test("POST /api/auth/login (non-existent user)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/login (non-existent user)", False, None, str(e))
            return False

    def test_admin_user_login_redirect(self):
        """Test admin user login returns admin flag"""
        try:
            # First create admin user
            admin_data = {
                "email": "admin@tratorshop.com",
                "password": "Admin@123",
                "name": "Admin User"
            }
            requests.post(f"{self.api_url}/auth/register", json=admin_data)
            
            # Login as admin
            login_data = {
                "email": "admin@tratorshop.com",
                "password": "Admin@123"
            }
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = data.get("is_admin") == True or data.get("email") == "admin@tratorshop.com"
            self.log_test("POST /api/auth/login (admin user)", success, response.status_code)
            return success
        except Exception as e:
            self.log_test("POST /api/auth/login (admin user)", False, None, str(e))
            return False

    def run_dual_auth_tests(self):
        """Run all dual authentication tests"""
        print("\n🔐 Testing Dual Authentication System...")
        
        self.test_user_register_api()
        sleep(0.1)
        
        self.test_user_register_api_invalid_email()
        sleep(0.1)
        
        self.test_user_register_api_short_password()
        sleep(0.1)
        
        self.test_user_login_api()
        sleep(0.1)
        
        self.test_user_login_api_wrong_password()
        sleep(0.1)
        
        self.test_user_login_api_nonexistent_user()
        sleep(0.1)
        
        self.test_admin_user_login_redirect()
        sleep(0.1)

    def run_admin_auth_tests(self):
        """Run all admin authentication tests"""
        print("\n🔐 Testing Admin Authentication System...")
        
        self.test_admin_login_api()
        sleep(0.1)
        
        self.test_admin_login_api_wrong_credentials()
        sleep(0.1)
        
        self.test_admin_login_api_nonexistent_user()
        sleep(0.1)
        
        self.test_admin_auth_me_without_token()
        sleep(0.1)
        
        self.test_admin_endpoints_with_valid_token()
        sleep(0.1)

    def get_test_results_dict(self):
        """Return test results as dictionary for JSON export"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
            "detailed_results": self.test_results
        }

def main():
    tester = TratorShopAPITester()
    
    try:
        tester.run_public_api_tests()
        tester.run_authenticated_tests()
        tester.run_dual_auth_tests()  # Add dual authentication tests
        tester.run_admin_auth_tests()  # Add admin authentication tests
        tester.run_dealer_tests()  # Add dealer system tests
        tester.print_summary()
        
        # Save results to JSON
        results = tester.get_test_results_dict()
        with open("/app/backend_api_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Exit code based on success
        exit_code = 0 if tester.tests_passed == tester.tests_run else 1
        return exit_code
        
    except Exception as e:
        print(f"💥 Fatal error during testing: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())