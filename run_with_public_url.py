from app import app
import os
import subprocess
import time
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_flask():
    # Run Flask on port 5000
    app.run(port=5000)

def run_ngrok():
    import json
    import requests
    from urllib.request import urlopen
    
    # Kill any existing ngrok processes
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], capture_output=True)
        time.sleep(2)
    except:
        pass

    try:
        # Start ngrok without auth
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '5000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print('\nStarting ngrok tunnel...')
        
        # Wait for ngrok to initialize and get public URL
        max_retries = 10
        public_url = None
        
        for i in range(max_retries):
            try:
                time.sleep(2)  # Wait between retries
                response = urlopen('http://localhost:4040/api/tunnels')
                data = json.loads(response.read())
                if data['tunnels']:
                    public_url = data['tunnels'][0]['public_url']
                    break
            except Exception:
                if i < max_retries - 1:  # Don't print retrying on last attempt
                    print(f'Waiting for ngrok to initialize... ({i+1}/{max_retries})')
                continue
        
        if public_url:
            print('\nNgrok tunnel established!')
            print(f'Public URL: {public_url}')
            print('\nShare this URL to access your application\n')
        else:
            print('\nNgrok started but could not get public URL.')
            print('Please:')
            print('1. Open http://localhost:4040 in your browser')
            print('2. Look for your public URL there')
            print('3. If nothing appears, restart the application\n')
            
    except Exception as e:
        print(f'\nError starting ngrok: {str(e)}')
        print('\nPlease ensure ngrok is installed:')
        print('1. winget install Ngrok.Ngrok')
        print('2. Close all terminals')
        print('3. Open new terminal and try again\n')
        exit(1)

if __name__ == '__main__':
    print('Starting Cricket Registration Application with public URL...')
    
    # Start ngrok in a separate thread
    ngrok_thread = Thread(target=run_ngrok, daemon=True)
    ngrok_thread.start()
    
    # Give ngrok time to initialize before starting Flask
    time.sleep(5)
    
    # Start Flask app
    print('\nStarting Flask application...')
    run_flask()
public_url = tunnel.public_url

print(f'\nPublic URLs:')
print(f'Registration URL: {public_url}')
print(f'Webhook URL: {public_url}/api/upi-webhook')
print(f'Payment Updates SSE URL: {public_url}/stream')

# Run the Flask application with host specified to allow external access
app.run(host='0.0.0.0', port=5000)