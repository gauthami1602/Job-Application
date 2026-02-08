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
api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key) if api_key else None

def search_github_jobs():
    """Search GitHub Jobs for matching positions with retry logic"""
    jobs = []
    try:
        url = "https://jobs.github.com/positions.json"
        
        for title in JOB_TITLES:
            params = {
                "description": title,
                "location": "remote"
            }
            
            # Retry logic
            for attempt in range(3):
                try:
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
                                "description": job.get("description", "")[:500],
                                "source": "GitHub Jobs"
                            })
                        break  # Success, exit retry loop
                    elif response.status_code == 429:  # Rate limited
                        print(f"GitHub Jobs rate limited, waiting 5 seconds...")
                        time.sleep(5)
                    else:
                        print(f"GitHub Jobs status: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"GitHub Jobs attempt {attempt + 1} failed: {str(e)[:100]}")
                    if attempt < 2:
                        time.sleep(3)
                    continue
                    
    except Exception as e:
        print(f"GitHub Jobs search error: {str(e)[:100]}")
    
    return jobs

def search_wellfound_jobs():
    """Search Wellfound for startup jobs with better error handling"""
    jobs = []
    try:
        # Try multiple search approaches
        search_queries = [
            {"q": "Product Manager", "location": "remote"},
            {"q": "Product Owner", "location": "remote"},
            {"q": "Project Manager", "location": "remote"},
            {"q": "Business Analyst", "location": "remote"},
        ]
        
        for query in search_queries:
            try:
                # Wellfound API endpoint (alternative approach)
                url = "https://wellfound.com/api/v3/jobs"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "application/json"
                }
                
                params = {
                    "query": query.get("q"),
                    "location": query.get("location"),
                    "per_page": 25
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "jobs" in data:
                            for job in data["jobs"]:
                                jobs.append({
                                    "id": job.get("id"),
                                    "title": job.get("title"),
                                    "company": job.get("startup", {}).get("name") if job.get("startup") else "Unknown",
                                    "location": job.get("location", "Remote"),
                                    "url": f"https://wellfound.com/jobs/{job.get('id')}",
                                    "description": job.get("description", "")[:500],
                                    "source": "Wellfound"
                                })
                    except Exception as e:
                        print(f"Wellfound JSON parse error: {str(e)[:100]}")
                        
            except requests.exceptions.RequestException as e:
                print(f"Wellfound request error: {str(e)[:100]}")
                continue
                
    except Exception as e:
        print(f"Wellfound search error: {str(e)[:100]}")
    
    return jobs

def search_linkedin_jobs_free():
    """Try to search LinkedIn jobs (limited free approach)"""
    jobs = []
    try:
        # LinkedIn has limited free API access
        # This is a simplified approach - for production, would need LinkedIn API key
        print("LinkedIn free API limited - skipping for now")
    except Exception as e:
        print(f"LinkedIn search error: {str(e)[:100]}")
    
    return jobs

def filter_and_rank_jobs(jobs):
    """Use Claude to filter and rank jobs by relevance to profile"""
    if not jobs:
        return "No jobs found to rank"
    
    if not client:
        print("⚠️  No Anthropic API key found - skipping Claude ranking")
        return "\n".join([f"{job['title']} at {job['company']} ({job['source']}) - {job['url']}" for job in jobs[:10]])
    
    # Create job listing text
    job_listing = "\n\n".join([
        f"Job {i+1}:\nTitle: {job['title']}\nCompany: {job['company']}\nLocation: {job['location']}\nSource: {job['source']}\nURL: {job['url']}\nDescription: {job['description']}"
        for i, job in enumerate(jobs[:30])  # Limit to top 30 for API efficiency
    ])
    
    # Use Claude to filter and rank
    prompt = f"""You are a job matching expert. I'm a Senior Full Stack Cloud Engineer with 7+ years of DevOps experience, 
expertise in ML operations pipelines, and a Master's in Business Analytics. I recently completed the NSF I-Corps program 
and co-founded MATXH, a healthcare startup focused on medication equivalency across countries.

I'm looking for Product Owner, Product Manager, Project Manager, or Business Analyst roles that are:
- Remote or Boston-based
- In the US
- At companies where my technical background would add significant value

Here are current job listings:

{job_listing}

Please:
1. Filter out jobs that don't match the criteria
2. Rank remaining jobs by relevance to my profile
3. For each job, briefly explain why it's a good match (1-2 sentences)
4. Return ONLY valid jobs in this format:

RANK | Title | Company | Why It Matches | URL

Be strict - only include genuinely relevant jobs."""

    try:
        message = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        return response_text
    
    except Exception as e:
        print(f"Claude ranking error: {str(e)[:100]}")
        # Fallback: just list the jobs
        return "\n".join([f"{job['title']} at {job['company']} ({job['source']}) - {job['url']}" for job in jobs[:10]])

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
          <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px;">
              <h2 style="color: #333;">🎯 Job Alerts - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</h2>
              <p style="color: #666; font-size: 16px;">Found <strong>{job_count}</strong> matching job opportunities for you:</p>
              <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
              <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 13px; line-height: 1.5;">
{jobs_text}
              </pre>
              <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
              <p style="color: #999; font-size: 12px; text-align: center;">
                ✅ Next check in 2 hours<br>
                💡 This is an automated job alert from your Claude job search system
              </p>
            </div>
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
        print(f"❌ Email send error: {str(e)[:100]}")
        return False

def run_job_search():
    """Main job search and alert function"""
    global LAST_JOB_IDS
    
    print(f"\n{'='*60}")
    print(f"🔍 Searching for jobs at {datetime.now().strftime('%I:%M %p')}...")
    print(f"{'='*60}")
    
    # Search all sources
    print("📌 Searching GitHub Jobs...")
    github_jobs = search_github_jobs()
    print(f"  Found {len(github_jobs)} jobs")
    
    print("📌 Searching Wellfound...")
    wellfound_jobs = search_wellfound_jobs()
    print(f"  Found {len(wellfound_jobs)} jobs")
    
    all_jobs = github_jobs + wellfound_jobs
    
    # Filter out duplicates and already seen jobs
    new_jobs = []
    for job in all_jobs:
        job_id = job.get("id", job.get("url"))
        if job_id not in LAST_JOB_IDS:
            new_jobs.append(job)
            LAST_JOB_IDS.add(job_id)
    
    print(f"\n📊 Summary:")
    print(f"  Total jobs found: {len(all_jobs)}")
    print(f"  New jobs since last check: {len(new_jobs)}")
    
    if new_jobs:
        print(f"\n🤖 Processing with Claude AI...")
        
        # Use Claude to filter and rank
        ranked_jobs = filter_and_rank_jobs(new_jobs)
        
        # Send email if we have good matches
        if "RANK" in ranked_jobs or len(ranked_jobs) > 100:
            print(f"✉️  Sending email digest...")
            send_email_digest(ranked_jobs, len(new_jobs))
        else:
            print("⚠️  No high-relevance matches in this batch - skipping email")
    else:
        print("ℹ️  No new jobs found since last check")
    
    print(f"⏳ Waiting {CHECK_INTERVAL//3600} hours until next check...\n")

def main():
    """Main loop - run every 2 hours"""
    print("\n" + "="*60)
    print("🚀 Job Alert System Starting...")
    print("="*60)
    print(f"Email: {GMAIL_ADDRESS}")
    print(f"Job Titles: {', '.join(JOB_TITLES)}")
    print(f"Locations: {', '.join(LOCATIONS)}")
    print(f"Check Interval: Every {CHECK_INTERVAL//3600} hours")
    print("="*60 + "\n")
    
    # Run immediately on start
    run_job_search()
    
    # Then run every 2 hours
    while True:
        time.sleep(CHECK_INTERVAL)
        run_job_search()

if __name__ == "__main__":
    main()
