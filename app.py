#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os
from github import Github, Auth
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
        repos = list(u.get_repos()[:7])
        
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
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return "❌ GOOGLE_API_KEY not found in .env file"
        
        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.9
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a brutal, savage code reviewer and GitHub profile roaster. 
Your job is to analyze GitHub profiles and roast them mercilessly.
Be absolutely ruthless. Keep it ONE PARAGRAPH. Make it hurt."""),
            ("user", "Roast this GitHub profile:\n\n{profile_data}")
        ])
        
        # Create chain
        chain = prompt | llm | StrOutputParser()
        
        # Execute
        result = chain.invoke({"profile_data": txt})
        return result
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

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