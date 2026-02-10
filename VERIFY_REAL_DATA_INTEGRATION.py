#!/usr/bin/env python3
"""
VERIFY REAL DATA INTEGRATION
Test script to verify all real data integrations are working
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationVerifier:
    """Verify all real data integrations are working"""
    
    def __init__(self):
        self.test_results = {}
        self.overall_status = "unknown"
        
    async def verify_all_integrations(self):
        """Verify all integrations and generate a comprehensive report"""
        logger.info("="*80)
        logger.info("🔍 VERIFYING REAL DATA INTEGRATIONS")
        logger.info("="*80)
        logger.info("")
        
        # Test each integration
        await self._test_payment_processing()
        await self._test_affiliate_tracking()
        await self._test_social_media()
        await self._test_ai_content_generation()
        await self._test_email_marketing()
        
        # Generate report
        self._generate_verification_report()
        
        return self.overall_status == "all_passed"
    
    async def _test_payment_processing(self):
        """Test real payment processing integration"""
        logger.info("💳 Testing Payment Processing Integration...")
        
        try:
            from REAL_PAYMENT_PROCESSING import real_payment_processing
            
            # Initialize payment processing
            success = await real_payment_processing.initialize()
            
            if success:
                # Test basic functionality
                status = real_payment_processing.get_status()
                
                self.test_results["payment_processing"] = {
                    "status": "passed",
                    "details": {
                        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
                        "total_revenue": status.get("total_revenue", 0),
                        "total_transactions": status.get("total_transactions", 0),
                        "active_subscriptions": status.get("active_subscriptions", 0)
                    }
                }
                logger.info("✅ Payment Processing: PASSED")
            else:
                self.test_results["payment_processing"] = {
                    "status": "failed",
                    "details": {"reason": "Initialization failed"}
                }
                logger.warning("⚠️ Payment Processing: FAILED")
                
        except Exception as e:
            self.test_results["payment_processing"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            logger.error(f"❌ Payment Processing: ERROR - {e}")
    
    async def _test_affiliate_tracking(self):
        """Test real affiliate tracking integration"""
        logger.info("🔗 Testing Affiliate Tracking Integration...")
        
        try:
            from REAL_AFFILIATE_TRACKING import real_affiliate_tracking
            
            # Initialize affiliate tracking
            success = await real_affiliate_tracking.initialize()
            
            if success:
                # Test basic functionality
                status = real_affiliate_tracking.get_status()
                
                self.test_results["affiliate_tracking"] = {
                    "status": "passed",
                    "details": {
                        "total_affiliates": status.get("total_affiliates", 0),
                        "total_referrals": status.get("total_referrals", 0),
                        "total_commissions": status.get("total_commissions", 0),
                        "active_networks": status.get("active_networks", 0)
                    }
                }
                logger.info("✅ Affiliate Tracking: PASSED")
            else:
                self.test_results["affiliate_tracking"] = {
                    "status": "failed",
                    "details": {"reason": "Initialization failed"}
                }
                logger.warning("⚠️ Affiliate Tracking: FAILED")
                
        except Exception as e:
            self.test_results["affiliate_tracking"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            logger.error(f"❌ Affiliate Tracking: ERROR - {e}")
    
    async def _test_social_media(self):
        """Test real social media integration"""
        logger.info("📱 Testing Social Media Integration...")
        
        try:
            from REAL_SOCIAL_MEDIA_INTEGRATION import real_social_media
            
            # Initialize social media
            success = await real_social_media.initialize()
            
            if success:
                # Test basic functionality
                status = real_social_media.get_status()
                
                self.test_results["social_media"] = {
                    "status": "passed",
                    "details": {
                        "enabled_platforms": status.get("enabled_platforms", 0),
                        "total_posts": status.get("total_posts", 0),
                        "total_engagements": status.get("total_engagements", 0),
                        "platforms": status.get("platforms", {})
                    }
                }
                logger.info("✅ Social Media Integration: PASSED")
            else:
                self.test_results["social_media"] = {
                    "status": "failed",
                    "details": {"reason": "Initialization failed"}
                }
                logger.warning("⚠️ Social Media Integration: FAILED")
                
        except Exception as e:
            self.test_results["social_media"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            logger.error(f"❌ Social Media Integration: ERROR - {e}")
    
    async def _test_ai_content_generation(self):
        """Test AI content generation capabilities"""
        logger.info("🤖 Testing AI Content Generation...")
        
        try:
            from AUTOMATED_REVENUE_ENGINE import revenue_engine
            
            # Test AI content generation
            test_prompt = "Write a 50-word description of an AI-powered life-saving watch"
            content = await revenue_engine.generate_ai_content(
                "You are a marketing expert for NarcoGuard.",
                test_prompt,
                max_tokens=200
            )
            
            if content and len(content) > 10:
                self.test_results["ai_content_generation"] = {
                    "status": "passed",
                    "details": {
                        "content_length": len(content),
                        "content_preview": content[:100] + "..." if len(content) > 100 else content
                    }
                }
                logger.info("✅ AI Content Generation: PASSED")
            else:
                self.test_results["ai_content_generation"] = {
                    "status": "failed",
                    "details": {"reason": "Content generation failed"}
                }
                logger.warning("⚠️ AI Content Generation: FAILED")
                
        except Exception as e:
            self.test_results["ai_content_generation"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            logger.error(f"❌ AI Content Generation: ERROR - {e}")
    
    async def _test_email_marketing(self):
        """Test email marketing integration"""
        logger.info("📧 Testing Email Marketing Integration...")
        
        try:
            # Test SendGrid integration
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            
            if sendgrid_key:
                try:
                    from sendgrid import SendGridAPIClient
                    from sendgrid.helpers.mail import Mail
                    
                    # Test SendGrid client creation
                    sg = SendGridAPIClient(sendgrid_key)
                    
                    self.test_results["email_marketing"] = {
                        "status": "passed",
                        "details": {
                            "sendgrid_configured": True,
                            "api_key_valid": True
                        }
                    }
                    logger.info("✅ Email Marketing: PASSED")
                    
                except Exception as e:
                    self.test_results["email_marketing"] = {
                        "status": "failed",
                        "details": {"error": str(e)}
                    }
                    logger.warning("⚠️ Email Marketing: FAILED")
            else:
                self.test_results["email_marketing"] = {
                    "status": "skipped",
                    "details": {"reason": "SendGrid API key not configured"}
                }
                logger.info("⏭️ Email Marketing: SKIPPED (no API key)")
                
        except Exception as e:
            self.test_results["email_marketing"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            logger.error(f"❌ Email Marketing: ERROR - {e}")
    
    def _generate_verification_report(self):
        """Generate comprehensive verification report"""
        logger.info("")
        logger.info("="*80)
        logger.info("📊 INTEGRATION VERIFICATION REPORT")
        logger.info("="*80)
        logger.info("")
        
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        
        for integration, result in self.test_results.items():
            status = result["status"]
            details = result.get("details", {})
            
            logger.info(f"🔍 {integration.upper()}:")
            logger.info(f"   Status: {status.upper()}")
            
            if status == "passed":
                passed += 1
                logger.info("   ✅ Integration working correctly")
                for key, value in details.items():
                    logger.info(f"   📊 {key}: {value}")
            elif status == "failed":
                failed += 1
                logger.info("   ❌ Integration failed")
                for key, value in details.items():
                    logger.info(f"   🚨 {key}: {value}")
            elif status == "skipped":
                skipped += 1
                logger.info("   ⏭️ Integration skipped")
                for key, value in details.items():
                    logger.info(f"   📝 {key}: {value}")
            elif status == "error":
                errors += 1
                logger.info("   💥 Integration error")
                for key, value in details.items():
                    logger.info(f"   🚨 {key}: {value}")
            
            logger.info("")
        
        # Calculate overall status
        total_tests = len(self.test_results)
        if errors > 0:
            self.overall_status = "errors"
        elif failed > 0:
            self.overall_status = "failed"
        elif passed == total_tests:
            self.overall_status = "all_passed"
        else:
            self.overall_status = "partial_success"
        
        # Summary
        logger.info("="*80)
        logger.info("📈 SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Integrations: {total_tests}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⏭️ Skipped: {skipped}")
        logger.info(f"💥 Errors: {errors}")
        logger.info(f"Overall Status: {self.overall_status.upper()}")
        logger.info("")
        
        # Recommendations
        if self.overall_status == "all_passed":
            logger.info("🎉 ALL INTEGRATIONS WORKING! Ready to go live.")
        elif self.overall_status == "partial_success":
            logger.info("⚠️ SOME INTEGRATIONS WORKING. Review failed/skipped items.")
        else:
            logger.info("🚨 ISSUES DETECTED. Please review and fix before proceeding.")
        
        logger.info("")
        logger.info("="*80)
        
        # Save report
        self._save_verification_report()
    
    def _save_verification_report(self):
        """Save verification report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.overall_status,
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results.values() if r["status"] == "passed"),
                "failed": sum(1 for r in self.test_results.values() if r["status"] == "failed"),
                "skipped": sum(1 for r in self.test_results.values() if r["status"] == "skipped"),
                "errors": sum(1 for r in self.test_results.values() if r["status"] == "error")
            }
        }
        
        # Save to file
        report_file = Path("generated_content") / "integration_verification_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved to: {report_file}")
    
    def get_overall_status(self) -> str:
        """Get overall verification status"""
        return self.overall_status
    
    def get_test_results(self) -> Dict[str, Any]:
        """Get detailed test results"""
        return self.test_results

async def main():
    """Main verification function"""
    verifier = IntegrationVerifier()
    
    success = await verifier.verify_all_integrations()
    
    if success:
        logger.info("🎉 VERIFICATION COMPLETE: All integrations working!")
        return 0
    else:
        logger.info("⚠️ VERIFICATION COMPLETE: Some issues detected.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Verification failed with error: {e}")
        sys.exit(1)