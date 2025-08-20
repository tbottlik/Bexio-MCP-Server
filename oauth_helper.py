#!/usr/bin/env python3
"""
OAuth helper script for Bexio access token generation.
This script helps you obtain an access token using the Authorization Code Flow.
"""

import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Bexio."""
    
    def do_GET(self):
        """Handle GET request with authorization code."""
        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            # Success - got authorization code
            auth_code = query_params['code'][0]
            self.server.auth_code = auth_code
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html>
            <body>
                <h1>Success!</h1>
                <p>Authorization code received. You can close this window and return to your terminal.</p>
                <script>setTimeout(function(){window.close();}, 3000);</script>
            </body>
            </html>
            ''')
        elif 'error' in query_params:
            # Error occurred
            error = query_params['error'][0]
            self.server.auth_error = error
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
            <html>
            <body>
                <h1>Error</h1>
                <p>OAuth error: {error}</p>
            </body>
            </html>
            '''.encode())
        
        # Signal that we're done
        self.server.callback_received = True
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def get_bexio_access_token():
    """Guide user through OAuth flow to get access token."""
    
    print("🔐 Bexio OAuth Access Token Generator")
    print("=" * 50)
    
    # Get client credentials
    print("\n📋 First, you need to set up your Bexio app:")
    print("1. Go to https://developer.bexio.com")
    print("2. Create a new app")
    print("3. Set redirect URL to: http://localhost:8080/callback")
    print("4. Note your Client ID and Client Secret")
    
    client_id = input("\n🔑 Enter your Client ID: ").strip()
    client_secret = input("🔒 Enter your Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Client ID and Secret are required!")
        return
    
    # OAuth parameters
    redirect_uri = "http://localhost:8080/callback"
    scope = "contact_show contact_edit kb_invoice_show kb_invoice_edit kb_offer_show kb_offer_edit kb_order_show kb_order_edit pr_project_show pr_project_edit article_show article_edit"
    
    # Build authorization URL
    auth_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope,
        'state': 'bexio_mcp_auth'
    }
    
    auth_url = "https://auth.bexio.com/authorize?" + urllib.parse.urlencode(auth_params)
    
    print(f"\n🌐 Opening browser for authorization...")
    print(f"If it doesn't open automatically, visit: {auth_url}")
    
    # Start local server to receive callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None
    server.auth_error = None
    server.callback_received = False
    
    # Start server in background
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("⏳ Waiting for authorization... (complete the login in your browser)")
    
    # Wait for callback
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while not server.callback_received and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    server.shutdown()
    
    if server.auth_error:
        print(f"❌ Authorization failed: {server.auth_error}")
        return
    
    if not server.auth_code:
        print("❌ Timeout waiting for authorization")
        return
    
    print("✅ Authorization code received!")
    
    # Exchange code for token
    import httpx
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': server.auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    print("🔄 Exchanging code for access token...")
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "https://auth.bexio.com/token",
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_response = response.json()
            access_token = token_response.get('access_token')
            
            if access_token:
                print("\n🎉 Success! Your access token:")
                print("=" * 50)
                print(access_token)
                print("=" * 50)
                
                print(f"\n📝 Add this to your Claude Desktop config:")
                print(f'"BEXIO_ACCESS_TOKEN": "{access_token}"')
                
                # Save to .env file
                try:
                    with open('.env', 'w') as f:
                        f.write(f"BEXIO_ACCESS_TOKEN={access_token}\n")
                        f.write("BEXIO_API_URL=https://api.bexio.com/2.0\n")
                        f.write("BEXIO_TIMEOUT=120\n")
                    print(f"\n💾 Token saved to .env file")
                except Exception as e:
                    print(f"⚠️ Could not save to .env file: {e}")
                
            else:
                print("❌ No access token in response")
                print(f"Response: {token_response}")
                
    except Exception as e:
        print(f"❌ Token exchange failed: {e}")


if __name__ == "__main__":
    get_bexio_access_token()
