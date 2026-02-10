#!/usr/bin/env python3
"""
AUTOMATED GRANT PROPOSAL SUBMITTER
Automatically generates and submits grant proposals for NarcoGuard
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AutoGrantSubmitter:
    """Automatically generates and tracks grant proposals"""
    
    def __init__(self):
        self.grant_catalog_path = Path("grant_catalog.json")
        self.proposals_dir = Path("generated_content/proposals")
        self.submissions_log = Path("generated_content/grant_submissions.jsonl")
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        
    def load_grant_catalog(self):
        """Load grant opportunities"""
        if not self.grant_catalog_path.exists():
            return []
        
        with open(self.grant_catalog_path) as f:
            catalog = json.load(f)
        
        return catalog.get("grants", [])
    
    def get_eligible_grants(self):
        """Get grants we should apply to"""
        grants = self.load_grant_catalog()
        eligible = []
        
        for grant in grants:
            # Skip if already applied
            if self.has_applied(grant):
                continue
            
            # Check if open or rolling
            status = grant.get("status", "").lower()
            if status in ["open", "rolling"]:
                eligible.append(grant)
                continue
            
            # Check deadline
            deadline = grant.get("deadline")
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline.replace("T", " "))
                    if deadline_date > datetime.now():
                        eligible.append(grant)
                except:
                    pass
        
        return eligible
    
    def has_applied(self, grant):
        """Check if we've already applied to this grant"""
        if not self.submissions_log.exists():
            return False
        
        grant_name = grant.get("name", "")
        
        with open(self.submissions_log) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("grant_name") == grant_name:
                        return True
                except:
                    continue
        
        return False
    
    async def generate_proposal(self, grant):
        """Generate a grant proposal"""
        print(f"\n📝 Generating proposal for: {grant['name']}")
        
        try:
            from AUTOMATED_REVENUE_ENGINE import revenue_engine
            
            # Build comprehensive prompt
            system_prompt = """You are an expert grant writer with 20+ years experience in public health, 
            harm reduction, and medical technology grants. You write compelling, data-driven proposals 
            that win funding."""
            
            user_prompt = f"""
Write a complete, professional grant proposal for NarcoGuard to apply for the following opportunity:

**GRANT DETAILS:**
- Name: {grant['name']}
- Agency: {grant['agency']}
- Requested Amount: ${grant.get('recommended_request', grant.get('max_amount', 400000)):,}
- Focus Areas: {', '.join(grant.get('focus_areas', []))}
- Deadline: {grant.get('deadline', 'Rolling')}

**NARCOGUARD PROJECT OVERVIEW:**
NarcoGuard is an AI-powered wearable overdose detection and automatic naloxone delivery system. 
The NG2 Guardian Watch continuously monitors vital signs and can detect overdose symptoms in real-time, 
automatically deploying naloxone and alerting emergency services.

**KEY FACTS:**
- 80 units ready for Broome County, NY pilot deployment
- AI-powered vital sign monitoring (heart rate, SpO2, skin temperature, motion)
- Automatic naloxone delivery system
- Real-time emergency services notification
- Proven technology ready for immediate deployment
- Addresses the opioid crisis with innovative harm reduction
- Web app demo: https://v0-narcoguard-pwa-build.vercel.app
- Funding campaign: https://gofund.me/9acf270ea

**APPLICANT DETAILS:**
- Organization: NarcoGuard LLC (New York)
- Status: Reinstatement pending upon funding approval
- Location: Broome County, NY
- Focus: Opioid overdose prevention and harm reduction

**PROPOSAL REQUIREMENTS:**

Write a complete proposal including:

1. **Executive Summary** (1 page)
   - Compelling overview of NarcoGuard
   - The problem we solve
   - Our innovative solution
   - Expected impact

2. **Problem Statement** (2 pages)
   - Opioid crisis statistics (national and Broome County)
   - Current gaps in overdose response
   - Why existing solutions fall short
   - Urgency of the problem

3. **Proposed Solution** (3 pages)
   - Detailed description of NG2 Guardian Watch
   - How the technology works
   - AI-powered detection algorithms
   - Automatic naloxone delivery mechanism
   - Emergency services integration
   - Pilot deployment plan for Broome County

4. **Project Timeline** (1 page)
   - Month 1-3: Deployment preparation
   - Month 4-6: Pilot rollout (80 units)
   - Month 7-12: Data collection and analysis
   - Month 13-18: Expansion planning

5. **Budget** (2 pages)
   - Equipment costs (80 units @ $X each)
   - Training and deployment
   - Monitoring and support
   - Data analysis and reporting
   - Administrative costs
   - Total: ${grant.get('recommended_request', grant.get('max_amount', 400000)):,}

6. **Expected Outcomes** (1 page)
   - Lives saved (quantifiable)
   - Response time reduction
   - Community impact
   - Data for future scaling
   - Potential for statewide/national expansion

7. **Organizational Capacity** (1 page)
   - Team expertise
   - Technology readiness
   - Community partnerships
   - Commitment to reinstatement upon funding

8. **Sustainability Plan** (1 page)
   - Long-term funding strategy
   - Revenue model
   - Expansion opportunities
   - Partnership development

**TONE & STYLE:**
- Professional and data-driven
- Compassionate and human-centered
- Emphasize innovation and impact
- Use specific numbers and statistics
- Highlight urgency and readiness

**FORMAT:**
- Use clear headings and subheadings
- Include bullet points for key facts
- Write in active voice
- Keep paragraphs concise
- Use markdown formatting

Generate the complete proposal now:
"""
            
            # Generate proposal
            proposal = revenue_engine.generate_ai_content(system_prompt, user_prompt, max_tokens=4000)
            
            # Save proposal
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            agency_slug = grant['agency'].replace(' ', '_').replace('/', '_')[:30]
            filename = self.proposals_dir / f"narcoguard_proposal_{agency_slug}_{timestamp}.md"
            
            # Add metadata header
            metadata = f"""---
Grant: {grant['name']}
Agency: {grant['agency']}
Amount Requested: ${grant.get('recommended_request', grant.get('max_amount', 0)):,}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Deadline: {grant.get('deadline', 'Rolling')}
Status: Draft
---

"""
            
            full_proposal = metadata + proposal
            filename.write_text(full_proposal)
            
            print(f"   ✅ Proposal saved: {filename}")
            
            # Log submission
            self.log_submission(grant, filename)
            
            return filename
            
        except Exception as e:
            print(f"   ❌ Error generating proposal: {e}")
            return None
    
    def log_submission(self, grant, proposal_file):
        """Log that we've generated a proposal"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "grant_name": grant['name'],
            "agency": grant['agency'],
            "amount": grant.get('recommended_request', grant.get('max_amount', 0)),
            "proposal_file": str(proposal_file),
            "status": "generated",
            "deadline": grant.get('deadline'),
            "submission_url": grant.get('portal_url', grant.get('submission_address', 'N/A'))
        }
        
        with open(self.submissions_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    async def generate_submission_instructions(self, grant, proposal_file):
        """Generate instructions for manual submission"""
        instructions_file = proposal_file.parent / f"{proposal_file.stem}_SUBMISSION_INSTRUCTIONS.md"
        
        instructions = f"""# Grant Submission Instructions

## Grant Details
- **Grant**: {grant['name']}
- **Agency**: {grant['agency']}
- **Amount**: ${grant.get('recommended_request', grant.get('max_amount', 0)):,}
- **Deadline**: {grant.get('deadline', 'Rolling')}

## Proposal File
`{proposal_file.name}`

## Submission Process

### Option 1: Online Portal
1. Visit: {grant.get('portal_url', 'See contact info below')}
2. Create account / log in
3. Start new application
4. Copy/paste proposal sections into online form
5. Upload any required attachments
6. Submit before deadline

### Option 2: Email Submission
1. Email to: {grant.get('contact', 'See portal for contact')}
2. Subject: "Grant Application - NarcoGuard Overdose Prevention System"
3. Attach proposal as PDF
4. Include cover letter (see below)

### Option 3: Mail Submission
1. Print proposal
2. Mail to: {grant.get('submission_address', 'See portal for address')}
3. Send certified mail with tracking
4. Submit at least 1 week before deadline

## Cover Letter Template

```
[Date]

{grant.get('contact', '[Grant Contact]')}
{grant['agency']}

Dear Grant Review Committee,

I am writing to submit NarcoGuard's application for the {grant['name']} grant program. 
NarcoGuard is an innovative AI-powered wearable system that automatically detects overdoses 
and delivers naloxone, addressing the urgent opioid crisis in Broome County, NY.

We are requesting ${grant.get('recommended_request', grant.get('max_amount', 0)):,} to deploy 
80 NG2 Guardian Watch units in a pilot program that will save lives and generate critical 
data for scaling this life-saving technology.

Our proposal demonstrates:
- Proven technology ready for immediate deployment
- Clear community need and impact
- Sustainable long-term model
- Experienced team committed to success

Thank you for considering our application. We look forward to partnering with {grant['agency']} 
to combat the opioid crisis through innovative harm reduction technology.

Sincerely,

[Your Name]
NarcoGuard LLC
[Contact Information]
```

## Required Documents

Check if these are needed:
- [ ] Completed proposal
- [ ] Budget spreadsheet
- [ ] Letters of support
- [ ] Organizational documents
- [ ] 501(c)(3) status (or explanation of LLC status)
- [ ] Financial statements
- [ ] Team bios/CVs

## Follow-Up

After submission:
1. Save confirmation email/number
2. Mark calendar for follow-up (2 weeks)
3. Prepare for potential interview/presentation
4. Update grant_catalog.json with submission status

## Questions?

Contact: {grant.get('contact', 'See grant portal')}
Portal: {grant.get('portal_url', 'N/A')}

---
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        instructions_file.write_text(instructions)
        print(f"   📋 Submission instructions: {instructions_file}")
    
    async def run_automation(self):
        """Main automation loop"""
        print("🚀 AUTO GRANT SUBMITTER")
        print("="*80)
        
        # Get eligible grants
        eligible = self.get_eligible_grants()
        
        if not eligible:
            print("ℹ️  No eligible grants found")
            print("   Check grant_catalog.json for opportunities")
            return
        
        print(f"✅ Found {len(eligible)} eligible grants\n")
        
        # Generate proposals for each
        for grant in eligible:
            proposal_file = await self.generate_proposal(grant)
            
            if proposal_file:
                await self.generate_submission_instructions(grant, proposal_file)
                
                # Wait between generations to avoid rate limits
                await asyncio.sleep(2)
        
        print("\n" + "="*80)
        print("✅ GRANT AUTOMATION COMPLETE")
        print("="*80)
        print(f"\n📁 Proposals saved to: {self.proposals_dir}")
        print(f"📊 Submission log: {self.submissions_log}")
        print("\n🎯 Next steps:")
        print("1. Review generated proposals")
        print("2. Follow submission instructions for each grant")
        print("3. Track submissions in grant_submissions.jsonl")
        print("="*80)


async def main():
    """Main entry point"""
    submitter = AutoGrantSubmitter()
    await submitter.run_automation()


if __name__ == "__main__":
    asyncio.run(main())
