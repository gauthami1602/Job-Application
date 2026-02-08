import os
import time
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from anthropic import Anthropic

# Configuration
GMAIL_ADDRESS = "hgauthamigopal@gmail.com"
GMAIL_APP_PASSWORD = "adpvvojceheirsb"
JOB_TITLES = ["Product Owner", "Product Manager", "Project Manager", "Business Analyst"]
LOCATIONS = ["Remote", "Boston", "USA"]
CHECK_INTERVAL = 7200  # 2 hours in seconds
LAST_JOB_IDS = set()  # Track jobs we've already seen

# Initialize Anthropic client
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key) if api_key else None

def search_indeed_jobs():
    """Search Indeed for jobs matching criteria"""
    jobs = []
    try:
        # Indeed API endpoint (using free tier)
        for title in JOB_TITLES:
            url = f"https://api.indeed.com/ads/apisearch"
            params = {
                "publisher": os.getenv("INDEED_PUBLISHER_ID", ""),  # You'll add this
                "q": title,
                "l": "Remote",
                "sort": "date",
                "radius": 100,
                "st": "json",
                "limit": 25
            }
            
            # Note: Indeed requires publisher ID. For now, we'll use web scraping alternative
            # or you can sign up for Indeed API
    except Exception as e:
        print(f"Indeed search error: {e}")
    
    return jobs

def search_github_jobs():
    """Search GitHub Jobs for matching positions"""
    jobs = []
    try:
        url = "https://jobs.github.com/positions.json"
        
        for title in JOB_TITLES:
            params = {
                "description": title,
                "location": "remote"
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for job in data:
                    jobs.append({
                        "id": job.get("id"),
                        "title": job.get("title"),
                        "company": job.get("company"),
                        "location": job.get("location"),
                        "url": job.get("url"),
                        "description": job.get("description", ""),
                        "source": "GitHub Jobs"
                    })
    except Exception as e:
        print(f"GitHub Jobs search error: {e}")
    
    return jobs

def search_wellfound_jobs():
    """Search Wellfound for startup jobs"""
    jobs = []
    try:
        # Wellfound API
        url = "https://api.wellfound.com/api/v3/jobs"
        
        for title in JOB_TITLES:
            params = {
                "query": title,
                "location_names": ["Remote", "Boston"],
                "per_page": 50
            }
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "jobs" in data:
                    for job in data["jobs"]:
                        jobs.append({
                            "id": job.get("id"),
                            "title": job.get("title"),
                            "company": job.get("startup", {}).get("name"),
                            "location": job.get("location"),
                            "url": f"https://wellfound.com/jobs/{job.get('id')}",
                            "description": job.get("description", ""),
                            "source": "Wellfound"
                        })
    except Exception as e:
        print(f"Wellfound search error: {e}")
    
    return jobs

def filter_and_rank_jobs(jobs):
    """Use Claude to filter and rank jobs by relevance to profile"""
    if not jobs:
        return []
    
    # Create job listing text
    job_listing = "\n\n".join([
        f"Job {i+1}:\nTitle: {job['title']}\nCompany: {job['company']}\nLocation: {job['location']}\nSource: {job['source']}\nURL: {job['url']}\nDescription: {job['description'][:500]}"
        for i, job in enumerate(jobs[:50])  # Limit to top 50 for API efficiency
    ])
    
    # Use Claude to filter and rank
    prompt = f"""You are a job matching expert. I'm a Senior Full Stack Cloud Engineer with 7+ years of DevOps experience, 
expertise in ML operations pipelines, and a Master's in Business Analytics. I recently completed the NSF I-Corps program 
and co-founded a healthcare startup (MATXH).

I'm looking for Product Owner, Product Manager, Project Manager, or Business Analyst roles that are:
- Remote or Boston-based
- In the US
- At companies where my technical background would add value

Here are the current job listings:

{job_listing}

Please:
1. Filter out jobs that don't match the criteria (wrong location, wrong role type, etc.)
2. Rank the remaining jobs by relevance to my profile (1 = most relevant)
3. For each job, briefly explain why it's a good match (1-2 sentences)
4. Return ONLY valid jobs in this format:

Job ID | Rank | Title | Company | Why It Matches | URL

Be strict - only include jobs that are genuinely relevant."""

    try:
        message = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        return response_text
    
    except Exception as e:
        print(f"Claude ranking error: {e}")
        return "Error ranking jobs"

def send_email_digest(jobs_text, job_count):
    """Send email digest of matching jobs"""
    try:
        # Create email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 Job Alerts: {job_count} Matching Opportunities"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = GMAIL_ADDRESS
        
        # Create HTML version
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>Job Alerts - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</h2>
            <p>Found <strong>{job_count}</strong> matching job opportunities for you:</p>
            <hr>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">
{jobs_text}
            </pre>
            <hr>
            <p style="color: #666; font-size: 12px;">
              Next check in 2 hours. This is an automated job alert from your Claude job search system.
            </p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html, "html"))
        
        # Send email via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, GMAIL_ADDRESS, msg.as_string())
        
        print(f"✅ Email sent successfully at {datetime.now()}")
        return True
    
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False

def run_job_search():
    """Main job search and alert function"""
    global LAST_JOB_IDS
    
    print(f"\n🔍 Searching for jobs at {datetime.now().strftime('%I:%M %p')}...")
    
    # Search all sources
    all_jobs = []
    all_jobs.extend(search_github_jobs())
    all_jobs.extend(search_wellfound_jobs())
    
    # Filter out duplicates and already seen jobs
    new_jobs = []
    for job in all_jobs:
        job_id = job.get("id", job.get("url"))
        if job_id not in LAST_JOB_IDS:
            new_jobs.append(job)
            LAST_JOB_IDS.add(job_id)
    
    if new_jobs:
        print(f"Found {len(new_jobs)} new jobs. Processing with Claude...")
        
        # Use Claude to filter and rank
        ranked_jobs = filter_and_rank_jobs(new_jobs)
        
        # Send email if we have good matches
        if "Job ID" in ranked_jobs or len(ranked_jobs) > 50:
            send_email_digest(ranked_jobs, len(new_jobs))
        else:
            print("No high-relevance matches found in this batch")
    else:
        print("No new jobs found since last check")

def main():
    """Main loop - run every 2 hours"""
    print("🚀 Job Alert System Starting...")
    print(f"Email: {GMAIL_ADDRESS}")
    print(f"Job Titles: {', '.join(JOB_TITLES)}")
    print(f"Check Interval: Every 2 hours")
    print("=" * 50)
    
    # Run immediately on start
    run_job_search()
    
    # Then run every 2 hours
    while True:
        print(f"\n⏳ Waiting {CHECK_INTERVAL//3600} hours until next check...")
        time.sleep(CHECK_INTERVAL)
        run_job_search()

if __name__ == "__main__":
    main()
