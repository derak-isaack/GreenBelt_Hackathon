from agent_docs import policy_evaluation 
from flask import Flask 
import asyncio
from register import login_bp
from research import research_bp
from whistle import whistle_bp
from dashboard import dashboard_bp

app = Flask()

app.register_blueprint(login_bp, url_prefix="/auth")
app.register_blueprint(research_bp, url_prefix="/research")
app.register_blueprint(whistle_bp, url_prefix="/whistle")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

@app.get("/evaluate")
async def evaluate_policy():
    result = await policy_evaluation()
    return {"analysis": result} 


if __name__ == "__main__":
    app.run(debug=True)