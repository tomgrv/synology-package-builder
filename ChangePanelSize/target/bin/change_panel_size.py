#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class ChangePanelHandler(BaseHTTPRequestHandler):
    HDD_BAY_LIST = [
        "RACK_0_Bay", "RACK_2_Bay", "RACK_4_Bay", "RACK_8_Bay", 
        "RACK_10_Bay", "RACK_12_Bay", "RACK_12_Bay_2", "RACK_16_Bay",
        "RACK_20_Bay", "RACK_24_Bay", "RACK_60_Bay", "TOWER_1_Bay",
        "TOWER_2_Bay", "TOWER_4_Bay", "TOWER_4_Bay_J", "TOWER_4_Bay_S",
        "TOWER_5_Bay", "TOWER_6_Bay", "TOWER_8_Bay", "TOWER_12_Bay"
    ]
    
    def do_POST(self):
        if self.path == '/change_panel_size/api':
            self.handle_change_panel_api()
        else:
            self.send_error(404)
    
    def do_GET(self):
        if self.path == '/change_panel_size/info':
            self.handle_info_api()
        else:
            self.send_error(404)
    
    def handle_change_panel_api(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            hdd_bay = data.get('hdd_bay', '')
            ssd_bay = data.get('ssd_bay', '')
            
            # 입력 검증
            if hdd_bay not in self.HDD_BAY_LIST:
                self.send_json_response({'success': False, 'message': 'Invalid HDD_BAY'})
                return
            
            if not re.fullmatch(r'\d+X\d+', ssd_bay):
                self.send_json_response({'success': False, 'message': 'SSD_BAY format error'})
                return
            
            # 스크립트 실행
            try:
                subprocess.run(['/usr/sbin/storagepanel.sh', hdd_bay, ssd_bay], check=True)
                self.send_json_response({
                    'success': True,
                    'message': f'storagepanel.sh called: {hdd_bay}, {ssd_bay} successfully changed'
                })
            except subprocess.CalledProcessError as e:
                self.send_json_response({'success': False, 'message': f'storagepanel.sh execution failed: {e}'})
        
        except json.JSONDecodeError:
            self.send_json_response({'success': False, 'message': 'Invalid JSON'})
    
    def handle_info_api(self):
        self.send_json_response({'hdd_bay_list': self.HDD_BAY_LIST})
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8089), ChangePanelHandler)
    server.serve_forever()

