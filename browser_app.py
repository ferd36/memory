import http.server
import socketserver
import json
import os
import datetime
import time
import random
from urllib.parse import urlparse, parse_qs
import problems
from classes import Record
import sessions

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MemoryAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/api/games':
            self.send_json(self.get_games())
        elif url.path == '/api/problem':
            params = parse_qs(url.query)
            game_id = params.get('id', [None])[0]
            self.send_json(self.generate_problem(game_id))
        elif url.path == '/api/stats':
            self.send_json(sessions.load_session_statistics())
        elif url.path == '/api/evaluate':
            params = parse_qs(url.query)
            # This is tricky as we need the problem object. 
            # We'll expect the client to POST the problem data and their answer.
            pass 
        else:
            super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if url.path == '/api/save':
            self.handle_save(data)
        elif url.path == '/api/evaluate':
            self.send_json(self.handle_evaluate(data))
        else:
            self.send_error(404, "Not Found")

    def handle_evaluate(self, data):
        from classes import Problem
        pb_data = data['problem']
        user_input = data['user_input']
        
        # We need the actual game class if it has a custom evaluate_solution (like AnagramProblem)
        game_id = pb_data.get('name') # This is usually the game type
        all_problems = problems.create_problems_dict()
        
        target_cls = Problem # Default
        for cls in all_problems.keys():
            # Check if this class's format_name matches the problem name or if we can find it
            if problems.format_problem_name(cls.__name__).lower() == game_id.lower():
                target_cls = cls
                break
        
        pb = target_cls(
            name=pb_data['name'],
            memorize=pb_data['memorize'],
            prompt=pb_data['prompt'],
            solution=pb_data['solution'],
            exposure_ms=pb_data['exposure_ms'],
            problem_type=pb_data.get('problem_type', '')
        )
        # Some classes might need extra attributes (like AnagramProblem needing _dict_index)
        # This is complex without persistence. 
        # For Anagrams, it checks if it's a valid word in the dictionary.
        
        score = pb.evaluate_solution(user_input)
        return {'score': score}

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_games(self):
        all_problems = problems.create_problems_dict()
        game_list = []
        for cls in all_problems.keys():
            game_list.append({
                'id': cls.__name__,
                'name': problems.format_problem_name(cls.__name__),
                'class': cls.__name__
            })
        return sorted(game_list, key=lambda x: x['name'])

    def generate_problem(self, game_id):
        all_problems = problems.create_problems_dict()
        # Find class by name
        target_cls = None
        for cls in all_problems.keys():
            if cls.__name__ == game_id:
                target_cls = cls
                break
        
        if not target_cls:
            return {'error': 'Game not found'}
        
        pb = target_cls.create()
        # Store current problem in session-like way (or just send to client)
        # Since we are stateless here, we'll send the solution too? 
        # No, better keep it secure or just trust the client for this lab app.
        # Actually, evaluate logic is in Python, so the client must send it back.
        return pb.to_dict()

    def handle_save(self, data):
        # Data format from client: { date, start_time, total, perfect, records: [{pb_dict, response, ms, score}] }
        # Reconstruct Record objects
        reconstructed_records = []
        for r in data['records']:
            pb_data = r['problem']
            # We don't necessarily need the exact class for Record.to_dict(), just an object with to_dict()
            # But evaluate logic might be needed. 
            # Reconstruct a generic Problem for storage
            from classes import Problem
            pb = Problem(
                name=pb_data['name'],
                memorize=pb_data['memorize'],
                prompt=pb_data['prompt'],
                solution=pb_data['solution'],
                exposure_ms=pb_data['exposure_ms'],
                problem_type=pb_data.get('problem_type', '')
            )
            reconstructed_records.append(Record(pb, r['response'], r['response_ms'], r['score']))

        test_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
        sessions.save_session_data(
            test_date, 
            data['start_time'], 
            data['total_questions'], 
            data['correct_answers'], 
            reconstructed_records
        )
        self.send_json({'status': 'success'})

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MemoryAPIHandler) as httpd:
        print(f"Serving Memory Lab at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
