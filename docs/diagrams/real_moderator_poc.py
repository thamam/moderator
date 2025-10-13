#!/usr/bin/env python3
"""
REAL Moderator PoC - Actually demonstrates the value
This version:
1. Uses Claude (via subprocess) to REALLY generate code
2. Analyzes the ACTUAL generated code for real issues
3. Shows we can catch problems in code we didn't write
"""

import os
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Improvement:
    """Represents a potential code improvement"""
    type: str
    severity: str  # error, warning, info
    file: str
    line: int
    description: str
    suggestion: str


class RealClaudeWrapper:
    """Actually calls Claude Code CLI to generate real code"""
    
    def __init__(self, output_dir: str = "./claude-generated"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_project(self, description: str) -> Dict:
        """
        Actually call Claude Code CLI to generate a project
        This demonstrates REAL value - we don't know what Claude will generate!
        """
        print(f"[Claude] Calling real Claude Code CLI...")
        print(f"[Claude] Description: {description}")
        
        try:
            # Change to output directory
            original_dir = os.getcwd()
            os.chdir(self.output_dir)
            
            # Actually call Claude Code CLI
            # Note: This requires Claude Code CLI to be installed and authenticated
            cmd = [
                "claude", 
                "code",
                description,
                "--yes"  # Auto-approve
            ]
            
            print(f"[Claude] Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            os.chdir(original_dir)
            
            if result.returncode != 0:
                # If Claude Code isn't available, fall back to explanation
                return self._explain_what_would_happen()
            
            # Get list of files Claude actually created
            files_created = self._get_created_files()
            
            return {
                'status': 'success',
                'files_created': files_created,
                'output': result.stdout,
                'method': 'real_claude'
            }
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[Claude] Claude Code CLI not available: {e}")
            return self._explain_what_would_happen()
    
    def _explain_what_would_happen(self) -> Dict:
        """
        If Claude Code CLI isn't available, explain what WOULD happen
        and create a sample that Claude might generate
        """
        print("\n" + "="*60)
        print("⚠️  Claude Code CLI not available - Simulating what would happen")
        print("="*60)
        print("""
In a REAL execution:

1. Claude Code would receive: "Create a task management API with user authentication"

2. Claude would generate (unpredictably!):
   - Maybe Flask, maybe FastAPI
   - Maybe SQLite, maybe PostgreSQL  
   - Maybe basic auth, maybe JWT
   - Maybe with tests, maybe without
   - Maybe with error handling, maybe not

3. We DON'T KNOW what issues it would have!

This is the VALUE - finding issues in code WE DIDN'T WRITE!

For demonstration, here's what Claude MIGHT generate:
        """)
        
        # Create a sample that represents what Claude might actually generate
        # This is more realistic - good but imperfect code
        sample_code = '''from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # TODO: Move to environment variable
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Basic validation
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
    
    # Create user
    hashed_password = generate_password_hash(password)
    user = User(username=username, password_hash=hashed_password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'])
    
    return jsonify({'token': token}), 200

@app.route('/tasks', methods=['GET'])
def get_tasks():
    # Note: No authentication check here - security issue!
    tasks = Task.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'completed': t.completed
    } for t in tasks])

@app.route('/tasks', methods=['POST']) 
def create_task():
    data = request.get_json()
    
    # Missing: Authentication check
    # Missing: Input validation
    task = Task(
        title=data['title'],  # Could raise KeyError
        description=data.get('description'),
        user_id=1  # Hardcoded user ID - wrong!
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'message': 'Task created'}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)  # Debug mode in production?
'''
        
        # Write this more realistic sample
        with open(os.path.join(self.output_dir, "app.py"), "w") as f:
            f.write(sample_code)
            
        return {
            'status': 'simulated',
            'files_created': ['app.py'],
            'method': 'simulated_claude_output',
            'note': 'This represents what Claude MIGHT generate - good but imperfect code'
        }
    
    def _get_created_files(self) -> List[str]:
        """Get list of files created in output directory"""
        files = []
        for root, dirs, filenames in os.walk(self.output_dir):
            dirs[:] = [d for d in dirs if d != '.git']
            for filename in filenames:
                files.append(filename)
        return files


class RealCodeAnalyzer:
    """Analyzes code that we DIDN'T write - this is the real value!"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        
    def analyze_unknown_code(self) -> List[Improvement]:
        """
        Analyze code we've never seen before
        This is valuable because we're finding issues in code we didn't write!
        """
        improvements = []
        
        print("\n[Analyzer] Analyzing code we didn't write...")
        
        # Read and analyze whatever files exist
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    improvements.extend(self._analyze_real_python_file(filepath))
        
        # Check for missing critical files
        improvements.extend(self._check_missing_critical_files())
        
        return improvements
    
    def _analyze_real_python_file(self, filepath: str) -> List[Improvement]:
        """Analyze a Python file we've never seen before"""
        improvements = []
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
            content = ''.join(lines)
        
        filename = os.path.basename(filepath)
        print(f"  Analyzing: {filename}")
        
        # REAL ISSUES WE MIGHT FIND IN CLAUDE-GENERATED CODE:
        
        # 1. Security Issues
        for i, line in enumerate(lines, 1):
            # Hardcoded secrets
            if 'SECRET_KEY' in line and ('=' in line or ':' in line) and any(q in line for q in ['"', "'"]):
                if 'environ' not in line and 'getenv' not in line:
                    improvements.append(Improvement(
                        type='security',
                        severity='error',
                        file=filename,
                        line=i,
                        description='Hardcoded SECRET_KEY found',
                        suggestion='Use environment variables: os.environ.get("SECRET_KEY")'
                    ))
            
            # SQL injection risks
            if 'query' in line.lower() and 'f"' in line or "f'" in line:
                improvements.append(Improvement(
                    type='security',
                    severity='error',
                    file=filename,
                    line=i,
                    description='Potential SQL injection with f-string',
                    suggestion='Use parameterized queries'
                ))
            
            # Debug mode in production
            if 'debug=True' in line and '__main__' in content:
                improvements.append(Improvement(
                    type='security',
                    severity='warning',
                    file=filename,
                    line=i,
                    description='Debug mode enabled',
                    suggestion='Set debug=False for production'
                ))
        
        # 2. Missing Authentication
        if '@app.route' in content:
            # Check if routes have authentication
            route_lines = [i for i, line in enumerate(lines, 1) if '@app.route' in line]
            for route_line in route_lines:
                # Check next 10 lines for auth check
                check_area = lines[route_line:min(route_line+10, len(lines))]
                auth_found = any('token' in l or 'auth' in l or '@jwt_required' in l for l in check_area)
                if not auth_found and not any(pub in lines[route_line-1] for pub in ['/login', '/register', '/health']):
                    improvements.append(Improvement(
                        type='security',
                        severity='warning',
                        file=filename,
                        line=route_line,
                        description='Route may be missing authentication',
                        suggestion='Add authentication decorator or check'
                    ))
        
        # 3. Error Handling
        if 'def ' in content:
            functions = [i for i, line in enumerate(lines, 1) if line.strip().startswith('def ')]
            for func_line in functions:
                func_name = lines[func_line-1].split('(')[0].replace('def ', '').strip()
                # Look for try/except in function
                func_end = func_line
                for j in range(func_line, min(func_line+50, len(lines))):
                    if lines[j] and not lines[j][0].isspace() and lines[j].strip():
                        func_end = j
                        break
                func_body = ''.join(lines[func_line:func_end])
                if 'try:' not in func_body and any(risk in func_body for risk in ['request.', 'db.', 'open(', 'json.loads']):
                    improvements.append(Improvement(
                        type='error_handling',
                        severity='warning',
                        file=filename,
                        line=func_line,
                        description=f'Function {func_name} lacks error handling',
                        suggestion='Add try/except for potential failures'
                    ))
        
        # 4. Input Validation
        if 'request.get_json()' in content or 'request.json' in content:
            for i, line in enumerate(lines, 1):
                if "data['" in line or 'data["' in line:
                    # Check if there's validation nearby
                    surrounding = lines[max(0,i-3):min(len(lines),i+3)]
                    if not any('if ' in s and 'data' in s for s in surrounding):
                        improvements.append(Improvement(
                            type='validation',
                            severity='warning',
                            file=filename,
                            line=i,
                            description='Direct dictionary access without validation',
                            suggestion='Use data.get() with validation'
                        ))
        
        return improvements
    
    def _check_missing_critical_files(self) -> List[Improvement]:
        """Check for files that SHOULD exist but don't"""
        improvements = []
        files = os.listdir(self.project_dir)
        
        critical_files = {
            'requirements.txt': 'List all Python dependencies',
            '.env.example': 'Document required environment variables',
            'test_': 'Add unit tests for your API',
            '.gitignore': 'Exclude sensitive files from git',
            'README.md': 'Document how to run and use the API'
        }
        
        for file_pattern, suggestion in critical_files.items():
            if not any(file_pattern in f for f in files):
                improvements.append(Improvement(
                    type='missing_file',
                    severity='warning' if file_pattern != 'requirements.txt' else 'error',
                    file='',
                    line=0,
                    description=f'Missing {file_pattern}',
                    suggestion=suggestion
                ))
        
        return improvements


def main():
    """Main execution showing REAL value"""
    print("=" * 60)
    print("🚀 REAL Moderator PoC - Finding Issues in Unknown Code")
    print("=" * 60)
    
    # Real project request
    description = "Create a task management API with user authentication, SQLite database, and JWT tokens"
    
    print(f"\n[Step 1] Generating REAL code with Claude...")
    print(f"Request: {description}\n")
    
    # Try to use real Claude
    wrapper = RealClaudeWrapper(output_dir="./claude-generated")
    result = wrapper.generate_project(description)
    
    print(f"\n[Step 2] Generated via: {result['method']}")
    print(f"Files created: {', '.join(result['files_created'])}")
    
    # Now analyze code we've never seen before!
    print(f"\n[Step 3] Analyzing the generated code for issues...")
    analyzer = RealCodeAnalyzer(wrapper.output_dir)
    improvements = analyzer.analyze_unknown_code()
    
    # Show what we found
    print(f"\n[RESULTS] Found {len(improvements)} issues in Claude-generated code:\n")
    
    errors = [i for i in improvements if i.severity == 'error']
    warnings = [i for i in improvements if i.severity == 'warning']
    
    if errors:
        print(f"🔴 Critical Issues ({len(errors)}):")
        for imp in errors:
            print(f"  - {imp.file}:{imp.line} - {imp.description}")
            print(f"    Fix: {imp.suggestion}\n")
    
    if warnings:
        print(f"🟡 Warnings ({len(warnings)}):")
        for imp in warnings[:5]:  # First 5
            print(f"  - {imp.file}:{imp.line} - {imp.description}")
    
    # The VALUE proposition
    print("\n" + "=" * 60)
    print("💡 THE VALUE DEMONSTRATED:")
    print("=" * 60)
    print("""
1. We asked Claude to generate code (or simulated it)
2. We DON'T KNOW what Claude would generate
3. We found REAL issues in that code:
   - Security vulnerabilities
   - Missing authentication
   - No error handling
   - Input validation issues
   
This is VALUABLE because:
- Every AI tool generates imperfect code
- Moderator catches these issues automatically
- Works with ANY code generation backend
- Gets better over time as patterns emerge

Imagine this running on EVERY piece of generated code!
    """)
    print("=" * 60)


if __name__ == "__main__":
    main()
