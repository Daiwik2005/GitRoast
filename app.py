#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import requests
import os
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_gh(user):
    token = os.getenv('GITHUB_API')
    if not token:
        return None, "GitHub API token not found"
    
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        u = g.get_user(user)
        repos = list(u.get_repos()[:5])
        
        info = f"{user} | Repos: {u.public_repos} | Followers: {u.followers} | Bio: {u.bio or 'None'}\n"
        info += "Top Repos: "
        
        repo_list = []
        for r in repos:
            lang = r.language or "?"
            stars = r.stargazers_count
            repo_list.append(f"{r.name}({lang})*{stars}")
        
        info += ", ".join(repo_list)
        
        user_data = {
            'username': user,
            'repos': u.public_repos,
            'followers': u.followers,
            'following': u.following,
            'bio': u.bio or 'None',
            'avatar': u.avatar_url,
            'top_repos': repo_list
        }
        
        return user_data, info
    except Exception as e:
        return None, str(e)

def roast(txt):
    try:
     data = {"model": "llama3.2:latest", "prompt": f"Roast this GitHub profile brutally in one paragraph:\n\n{txt}", "stream": False}
     return requests.post("http://localhost:11434/api/generate", json=data).json()['response']
    except Exception as e:
     return f"Error generating roast: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/roast', methods=['POST'])
def roast_profile():
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    user = url.rstrip('/').split('/')[-1]
    
    user_data, info = get_gh(user)
    if not user_data:
        return jsonify({'error': info}), 400
    
    roast_text = roast(info)
    
    return jsonify({
        'user': user_data,
        'roast': roast_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080)
