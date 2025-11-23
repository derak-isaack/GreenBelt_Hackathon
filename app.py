from agent_docs import policy_evaluation
from flask import Flask, request
import asyncio
from register import login_bp
from research import research_bp
from whistle import whistle_bp
from dashboard import dashboard_bp
from admin import admin_bp
from flask_cors import CORS
from analysis import ndvi_bp

# app = Flask()
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


app.register_blueprint(login_bp, url_prefix="/auth")
app.register_blueprint(research_bp, url_prefix="/research")
app.register_blueprint(whistle_bp, url_prefix="/whistle")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(ndvi_bp, url_prefix="/ndvi")
# app.register_blueprint(login_bp, url_prefix="/auth")

@app.get("/evaluate")
async def evaluate_policy():
    forest = request.args.get("forest")
    if not forest:
        return {"error": "Forest parameter is required"}, 400
    result = await policy_evaluation(forest)
    return {"analysis": result}


if __name__ == "__main__":
    app.run(debug=True)