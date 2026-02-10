#!/usr/bin/env python3
"""
REAL PAYMENT PROCESSING SYSTEM
Replaces simulation with real Stripe integration for CHATTY
"""

import asyncio
import stripe
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os
from dotenv import load_dotenv
from transparency_log import log_transparency

# Load environment variables
load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealPaymentProcessing:
    """Real payment processing system with Stripe integration"""
    
    def __init__(self):
        self.stripe_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.is_running = False
        
        # Configure Stripe
        if self.stripe_key:
            stripe.api_key = self.stripe_key
            logger.info("✅ Stripe API configured")
        else:
            logger.error("❌ Stripe API key not found - payment processing disabled")
            
        # Payment tracking
        self.total_revenue = 0.0
        self.transactions = []
        self.subscriptions = []
        self.failed_payments = []
        self.last_stripe_sync = 0
        self.sync_interval = 300  # 5 minutes
        
        # Product catalog
        self.products = {
            "basic_subscription": {
                "name": "Basic Subscription",
                "price": 29.99,
                "currency": "usd",
                "interval": "month",
                "description": "Basic access to CHATTY automation"
            },
            "premium_subscription": {
                "name": "Premium Subscription", 
                "price": 99.99,
                "currency": "usd",
                "interval": "month",
                "description": "Full access to all CHATTY features"
            },
            "enterprise_subscription": {
                "name": "Enterprise Subscription",
                "price": 499.99,
                "currency": "usd", 
                "interval": "month",
                "description": "Enterprise-grade CHATTY with custom features"
            },
            "one_time_donation": {
                "name": "Support NarcoGuard",
                "price": 25.00,
                "currency": "usd",
                "interval": None,
                "description": "One-time donation to support NarcoGuard development"
            }
        }
        
        # Affiliate tracking
        self.affiliate_commissions = []
        self.affiliate_partners = {}
        
    async def initialize(self):
        """Initialize payment processing system"""
        logger.info("💳 Initializing Real Payment Processing System...")
        
        if not self.stripe_key:
            logger.error("❌ Cannot initialize - Stripe key required")
            return False
            
        try:
            # Verify Stripe connection
            account = stripe.Account.retrieve()
            logger.info(f"✅ Connected to Stripe account: {account.id}")
            
            # Sync existing data
            await self.sync_stripe_data()
            
            # Create products if they don't exist
            await self.setup_product_catalog()
            
            logger.info("✅ Payment processing system initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Payment processing initialization failed: {e}")
            return False
    
    async def setup_product_catalog(self):
        """Set up Stripe product catalog"""
        try:
            # Check if products exist, create if needed
            for product_key, product_data in self.products.items():
                try:
                    # Check if product exists
                    products = stripe.Product.list(limit=100)
                    existing_product = None
                    for p in products:
                        if p.name == product_data["name"]:
                            existing_product = p
                            break
                    
                    if not existing_product:
                        # Create product
                        product = stripe.Product.create(
                            name=product_data["name"],
                            description=product_data["description"],
                            metadata={"product_key": product_key}
                        )
                        
                        # Create price
                        if product_data["interval"]:
                            # Subscription price
                            price = stripe.Price.create(
                                product=product.id,
                                unit_amount=int(product_data["price"] * 100),
                                currency=product_data["currency"],
                                recurring={"interval": product_data["interval"]}
                            )
                        else:
                            # One-time price
                            price = stripe.Price.create(
                                product=product.id,
                                unit_amount=int(product_data["price"] * 100),
                                currency=product_data["currency"]
                            )
                        
                        logger.info(f"✅ Created product: {product_data['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to create product {product_data['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Product catalog setup failed: {e}")
    
    async def sync_stripe_data(self):
        """Sync existing Stripe data"""
        try:
            # Sync charges
            charges = stripe.Charge.list(limit=100)
            for charge in charges:
                if charge.status == "succeeded":
                    self._process_charge(charge)
            
            # Sync subscriptions
            subscriptions = stripe.Subscription.list(limit=100)
            for subscription in subscriptions:
                self._process_subscription(subscription)
                
            logger.info(f"✅ Synced {len(self.transactions)} transactions and {len(self.subscriptions)} subscriptions")
            
        except Exception as e:
            logger.error(f"❌ Stripe data sync failed: {e}")
    
    def _process_charge(self, charge):
        """Process a Stripe charge"""
        transaction = {
            "id": charge.id,
            "amount": charge.amount / 100,
            "currency": charge.currency,
            "description": charge.description,
            "customer": charge.customer,
            "created": datetime.fromtimestamp(charge.created).isoformat(),
            "status": charge.status
        }
        
        self.transactions.append(transaction)
        self.total_revenue += transaction["amount"]
        
        log_transparency(
            "stripe_charge_processed",
            "ok",
            {
                "charge_id": charge.id,
                "amount": transaction["amount"],
                "currency": transaction["currency"]
            }
        )
    
    def _process_subscription(self, subscription):
        """Process a Stripe subscription"""
        sub_data = {
            "id": subscription.id,
            "customer": subscription.customer,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "created": datetime.fromtimestamp(subscription.created).isoformat()
        }
        
        self.subscriptions.append(sub_data)
    
    async def create_payment_intent(self, amount: float, currency: str = "usd", description: str = "CHATTY Payment") -> Dict[str, Any]:
        """Create a payment intent for one-time payments"""
        try:
            if not self.stripe_key:
                return {"error": "Stripe not configured"}
            
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency,
                description=description,
                automatic_payment_methods={"enabled": True}
            )
            
            logger.info(f"✅ Created payment intent: {intent.id} for ${amount}")
            return {"success": True, "client_secret": intent.client_secret, "payment_intent_id": intent.id}
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Payment intent creation failed: {e}")
            return {"error": str(e)}
    
    async def create_subscription(self, customer_email: str, product_key: str, affiliate_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a subscription for a customer"""
        try:
            if not self.stripe_key:
                return {"error": "Stripe not configured"}
            
            if product_key not in self.products:
                return {"error": "Invalid product"}
            
            product_data = self.products[product_key]
            
            # Create customer if doesn't exist
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers:
                customer = customers[0]
            else:
                customer = stripe.Customer.create(
                    email=customer_email,
                    metadata={"affiliate_id": affiliate_id} if affiliate_id else {}
                )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    "price_data": {
                        "currency": product_data["currency"],
                        "unit_amount": int(product_data["price"] * 100),
                        "product_data": {
                            "name": product_data["name"],
                            "description": product_data["description"]
                        },
                        "recurring": {"interval": product_data["interval"]}
                    }
                }],
                expand=["latest_invoice.payment_intent"]
            )
            
            # Track affiliate commission
            if affiliate_id:
                await self._track_affiliate_commission(customer.id, subscription.id, product_data["price"], affiliate_id)
            
            logger.info(f"✅ Created subscription: {subscription.id} for {customer_email}")
            return {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "status": subscription.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Subscription creation failed: {e}")
            return {"error": str(e)}
    
    async def _track_affiliate_commission(self, customer_id: str, subscription_id: str, amount: float, affiliate_id: str):
        """Track affiliate commission for a subscription"""
        commission_rate = 0.10  # 10% commission
        commission_amount = amount * commission_rate
        
        commission = {
            "id": f"com_{int(time.time())}",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "affiliate_id": affiliate_id,
            "amount": commission_amount,
            "rate": commission_rate,
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        
        self.affiliate_commissions.append(commission)
        
        # Store affiliate partner if new
        if affiliate_id not in self.affiliate_partners:
            self.affiliate_partners[affiliate_id] = {
                "id": affiliate_id,
                "total_commissions": 0,
                "active_referrals": 0,
                "created": datetime.now().isoformat()
            }
        
        self.affiliate_partners[affiliate_id]["total_commissions"] += commission_amount
        self.affiliate_partners[affiliate_id]["active_referrals"] += 1
        
        logger.info(f"✅ Tracked affiliate commission: ${commission_amount} for {affiliate_id}")
    
    async def process_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        try:
            if not self.stripe_webhook_secret:
                return {"error": "Webhook secret not configured"}
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                logger.info(f"✅ Payment succeeded: {payment_intent['id']}")
                
            elif event['type'] == 'charge.succeeded':
                charge = event['data']['object']
                self._process_charge(charge)
                
            elif event['type'] == 'customer.subscription.created':
                subscription = event['data']['object']
                self._process_subscription(subscription)
                
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                logger.warning(f"❌ Payment failed: {invoice['id']}")
                self.failed_payments.append({
                    "invoice_id": invoice['id'],
                    "customer": invoice['customer'],
                    "amount": invoice['amount_due'] / 100,
                    "reason": invoice.get('failure_reason', 'Unknown'),
                    "created": datetime.now().isoformat()
                })
            
            return {"success": True, "event_type": event['type']}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Webhook signature verification failed: {e}")
            return {"error": "Invalid signature"}
        except Exception as e:
            logger.error(f"❌ Webhook processing failed: {e}")
            return {"error": str(e)}
    
    async def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get revenue analytics and insights"""
        try:
            # Calculate monthly recurring revenue (MRR)
            active_subscriptions = [s for s in self.subscriptions if s["status"] == "active"]
            mrr = sum(self.products.get("premium_subscription", {}).get("price", 0) for s in active_subscriptions)
            
            # Calculate churn rate
            canceled_subscriptions = [s for s in self.subscriptions if s["status"] == "canceled"]
            churn_rate = len(canceled_subscriptions) / len(self.subscriptions) if self.subscriptions else 0
            
            # Calculate affiliate revenue
            total_affiliate_commissions = sum(c["amount"] for c in self.affiliate_commissions if c["status"] == "paid")
            
            # Calculate conversion rates
            total_customers = len(set(t["customer"] for t in self.transactions))
            conversion_rate = len(active_subscriptions) / total_customers if total_customers > 0 else 0
            
            analytics = {
                "total_revenue": self.total_revenue,
                "mrr": mrr,
                "total_transactions": len(self.transactions),
                "active_subscriptions": len(active_subscriptions),
                "total_customers": total_customers,
                "churn_rate": churn_rate,
                "conversion_rate": conversion_rate,
                "total_affiliate_commissions": total_affiliate_commissions,
                "total_affiliates": len(self.affiliate_partners),
                "failed_payments": len(self.failed_payments),
                "last_updated": datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Analytics calculation failed: {e}")
            return {"error": str(e)}
    
    async def start(self):
        """Start the payment processing system"""
        self.is_running = True
        logger.info("💳 Starting Real Payment Processing System...")
        
        # Start background sync
        asyncio.create_task(self._background_sync())
        
        logger.info("✅ Payment processing system running")
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(60)
    
    async def _background_sync(self):
        """Background task to sync Stripe data"""
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_stripe_sync > self.sync_interval:
                    await self.sync_stripe_data()
                    self.last_stripe_sync = current_time
                    
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Background sync error: {e}")
                await asyncio.sleep(300)
    
    async def stop(self):
        """Stop the payment processing system"""
        self.is_running = False
        logger.info("💳 Stopping Real Payment Processing System...")
        
        # Save state
        await self._save_state()
        
        logger.info("✅ Payment processing system stopped")
    
    async def _save_state(self):
        """Save payment processing state"""
        state = {
            "total_revenue": self.total_revenue,
            "transactions": self.transactions,
            "subscriptions": self.subscriptions,
            "failed_payments": self.failed_payments,
            "affiliate_commissions": self.affiliate_commissions,
            "affiliate_partners": self.affiliate_partners
        }
        
        state_file = Path("generated_content") / "payment_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"💾 Payment state saved to {state_file}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get payment processing status"""
        return {
            "status": "running" if self.is_running else "stopped",
            "stripe_configured": bool(self.stripe_key),
            "total_revenue": self.total_revenue,
            "total_transactions": len(self.transactions),
            "active_subscriptions": len([s for s in self.subscriptions if s["status"] == "active"]),
            "total_customers": len(set(t["customer"] for t in self.transactions)),
            "failed_payments": len(self.failed_payments),
            "total_affiliates": len(self.affiliate_partners),
            "total_commissions": sum(c["amount"] for c in self.affiliate_commissions)
        }

# Global instance
real_payment_processing = RealPaymentProcessing()

async def main():
    """Test the payment processing system"""
    if await real_payment_processing.initialize():
        await real_payment_processing.start()

if __name__ == "__main__":
    print("💳 REAL PAYMENT PROCESSING SYSTEM")
    print("=" * 60)
    print("Real Stripe integration for CHATTY")
    print("Replaces all simulation with real payment processing")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        asyncio.run(real_payment_processing.stop())