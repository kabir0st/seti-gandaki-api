#!/usr/bin/env python3
"""
Test script for the attendance logs endpoint
Usage examples:
1. Basic usage: python test_attendance_logs.py
2. With date range: python test_attendance_logs.py --staff-id 6 --date-from 2024-01-01 --date-to 2024-01-31
"""

import requests
import json
import argparse
from datetime import datetime, timedelta

def test_attendance_logs(base_url="http://localhost:8000", staff_id=6, date_from=None, date_to=None, token=None):
    """Test the attendance logs endpoint"""
    
    # Construct URL
    url = f"{base_url}/api/hrm/attendances/logs/"
    
    # Prepare parameters
    params = {'staff_id': staff_id}
    if date_from:
        params['date_from'] = date_from
    if date_to:
        params['date_to'] = date_to
    
    # Prepare headers
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    print(f"Testing attendance logs endpoint...")
    print(f"URL: {url}")
    print(f"Parameters: {params}")
    print("-" * 50)
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.startswith('X-'):
                print(f"  {key}: {value}")
        
        print("\nResponse Body:")
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response.text}")

def main():
    parser = argparse.ArgumentParser(description='Test attendance logs endpoint')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--staff-id', type=int, default=6, help='Staff ID to query')
    parser.add_argument('--date-from', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='End date (YYYY-MM-DD)')
    parser.add_argument('--token', help='Authentication token')
    
    args = parser.parse_args()
    
    # If no date range provided, use last 30 days
    if not args.date_from and not args.date_to:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        args.date_from = start_date.strftime('%Y-%m-%d')
        args.date_to = end_date.strftime('%Y-%m-%d')
        print(f"No date range provided, using last 30 days: {args.date_from} to {args.date_to}")
    
    test_attendance_logs(
        base_url=args.base_url,
        staff_id=args.staff_id,
        date_from=args.date_from,
        date_to=args.date_to,
        token=args.token
    )

if __name__ == '__main__':
    main()