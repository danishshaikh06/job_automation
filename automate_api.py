from flask import Flask, request, jsonify
from flask_cors import CORS
from danish_job_bot import run_job_automation
import os
import logging
from datetime import datetime
import tempfile
import base64

app = Flask(__name__)

# ✅ Allow CORS for all origins (you can restrict this later)
CORS(app, origins=["*"])

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route("/apply", methods=["POST"])
def apply():
    try:
        # Handle both JSON and FormData requests
        if request.is_json:
            # Handle JSON data
            data = request.json
            logger.info("Received JSON request")
        else:
            # Handle FormData (file uploads)
            data = request.form.to_dict()
            logger.info("Received FormData request")
            
            # Handle file upload from FormData
            resume_file = request.files.get('resume')
            if resume_file:
                # Save uploaded file to temporary location
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.pdf',
                    prefix='resume_'
                )
                resume_file.save(temp_file.name)
                data['resume_path'] = temp_file.name
                logger.info(f"Saved uploaded resume to: {temp_file.name}")
        
        logger.info(f"Received application request: {data.get('search_term', 'unknown')}")
        
        # Validate required fields
        required_fields = ["search_term"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing or empty field: {field}"}), 400
        
        # Handle file uploads (base64 encoded or file paths)
        resume_path = handle_file_upload(data.get("resume_file"), data.get("resume_path"), "resume")
        if not resume_path:
            return jsonify({"error": "Resume file is required"}), 400
        
        cover_letter_path = handle_file_upload(data.get("cover_letter_file"), data.get("cover_letter_path"), "cover_letter")
        
        # Validate max_jobs is reasonable
        max_jobs = int(data.get("max_jobs", 5))
        if max_jobs < 1 or max_jobs > 5:  # Limited to 5 as requested
            return jsonify({"error": "max_jobs must be between 1 and 5"}), 400
        
        logger.info(f"Starting job application for: {data['search_term']}")
        
        # Run the automation
        result = run_job_automation(
            search_term=data["search_term"],
            resume_path=resume_path,
            max_jobs=max_jobs,
            location=data.get("location", ""),
            experience_level=data.get("experience_level", ""),
            job_type=data.get("job_type", ""),
            date_posted=data.get("date_posted", ""),
            platform=data.get("platform", "linkedin"),  # Added platform parameter
            cover_letter_path=cover_letter_path or ""
        )
        
        # Clean up temporary files
        cleanup_temp_files([resume_path, cover_letter_path])
        
        logger.info(f"Job application completed. Success: {result.get('success', False)}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Application failed: {str(e)}",
            "applied_count": 0,
            "total_processed": 0,
            "jobs": []  # Return empty jobs array for frontend
        }), 500

def handle_file_upload(file_data, file_path, file_type):
    """Handle file upload from base64 data or file path"""
    try:
        # If base64 data is provided, save it as temp file
        if file_data:
            try:
                # Decode base64 data
                file_content = base64.b64decode(file_data)
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix='.pdf',
                    prefix=f'{file_type}_'
                )
                temp_file.write(file_content)
                temp_file.close()
                
                logger.info(f"Created temporary {file_type} file: {temp_file.name}")
                return temp_file.name
                
            except Exception as e:
                logger.error(f"Error processing {file_type} file data: {e}")
                return None
        
        # If file path is provided, validate it exists
        elif file_path and os.path.exists(file_path):
            return file_path
            
        return None
        
    except Exception as e:
        logger.error(f"Error handling {file_type} upload: {e}")
        return None

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        if file_path and file_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
            except:
                pass

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy", 
        "message": "Job bot API is running",
        "timestamp": datetime.now().isoformat(),
        "environment": "cloud" if os.getenv('RENDER') else "local"
    })

@app.route("/test", methods=["POST"])
def test_endpoint():
    """Test endpoint to verify the bot setup without running full automation"""
    try:
        from danish_job_bot import setup_driver
        
        # Test browser setup
        driver = setup_driver()
        driver.get("https://www.linkedin.com")
        title = driver.title
        driver.quit()
        
        return jsonify({
            "success": True,
            "message": "Browser test successful",
            "title": title
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Browser test failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)