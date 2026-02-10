# Real Data Environment Setup

This guide helps you configure all the necessary API keys and environment variables for the real data integrations.

## Required Environment Variables

### Payment Processing (Stripe)
```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Optional: Stripe webhook endpoint
STRIPE_WEBHOOK_URL=https://your-domain.com/api/webhooks/stripe
```

### Affiliate Tracking
```bash
# Affiliate Network API Keys (choose which networks you want to use)
SHAREASALE_MERCHANT_ID=your_shareasale_merchant_id
SHAREASALE_TOKEN=your_shareasale_token

CJ_AFFILIATE_ID=your_commission_junction_id
CJ_AFFILIATE_TOKEN=your_commission_junction_token

IMPACT_API_KEY=your_impact_api_key
IMPACT_ADVERTISER_ID=your_impact_advertiser_id

REFERSION_API_KEY=your_refersion_api_key
REFERSION_API_SECRET=your_refersion_api_secret

# Local affiliate tracking
AFFILIATE_SECRET_KEY=your_affiliate_secret_key
CHATTY_BASE_URL=https://your-domain.com
```

### Social Media Integration
```bash
# Twitter/X API Keys
X_CONSUMER_KEY=your_twitter_consumer_key
X_CONSUMER_SECRET=your_twitter_consumer_secret
X_ACCESS_TOKEN=your_twitter_access_token
X_ACCESS_SECRET=your_twitter_access_secret
X_BEARER_TOKEN=your_twitter_bearer_token

# LinkedIn API Keys
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id
LINKEDIN_ORG_ID=your_linkedin_organization_id

# Facebook API Keys
FACEBOOK_PAGE_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# Instagram API Keys
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_BUSINESS_ACCOUNT=your_instagram_business_account_id

# YouTube API Keys
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_CHANNEL_ID=your_youtube_channel_id
```

### Email Marketing (SendGrid)
```bash
# SendGrid API Key
SENDGRID_API_KEY=your_sendgrid_api_key
```

### AI Content Generation
```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Google AI API Key
GOOGLE_API_KEY=your_google_api_key

# Groq API Key
GROQ_API_KEY=your_groq_api_key

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Hugging Face API Key
HUGGINGFACE_TOKEN=your_huggingface_token
HUGGINGFACE_MODEL=your_preferred_model
```

### Additional Integrations
```bash
# SEO Tools (optional)
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=your_google_search_console_credentials
GOOGLE_ANALYTICS_VIEW_ID=your_google_analytics_view_id

# Marketing Automation
GOOGLE_ADS_CUSTOMER_ID=your_google_ads_customer_id
GOOGLE_ADS_DEVELOPER_TOKEN=your_google_ads_developer_token
FACEBOOK_AD_ACCOUNT_ID=your_facebook_ad_account_id

# CRM Integration (optional)
HUBSPOT_API_KEY=your_hubspot_api_key
SALESFORCE_CLIENT_ID=your_salesforce_client_id
SALESFORCE_CLIENT_SECRET=your_salesforce_client_secret

# Analytics
MATOMO_SITE_ID=your_matomo_site_id
MATOMO_URL=your_matomo_url
```

## How to Get API Keys

### Stripe
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/register)
2. Create an account
3. Get your API keys from Developers > API keys
4. Set up webhooks in Developers > Webhooks

### Twitter/X
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Apply for API access
3. Create a project and app
4. Get your API keys and tokens

### LinkedIn
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app
3. Get your access token and person ID

### Facebook/Instagram
1. Go to [Facebook Developer Portal](https://developers.facebook.com/)
2. Create a Facebook App
3. Set up Pages and Instagram Business Account
4. Get your access tokens

### YouTube
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project
3. Enable YouTube Data API v3
4. Create API credentials

### SendGrid
1. Go to [SendGrid](https://sendgrid.com/)
2. Create an account
3. Get your API key from Settings > API Keys

### AI Services
- **OpenAI**: [OpenAI Platform](https://platform.openai.com/)
- **Anthropic**: [Anthropic Console](https://console.anthropic.com/)
- **Google AI**: [Google AI Studio](https://aistudio.google.com/)
- **Groq**: [Groq Cloud](https://console.groq.com/)
- **DeepSeek**: [DeepSeek Console](https://platform.deepseek.com/)
- **Hugging Face**: [Hugging Face Hub](https://huggingface.co/)

## Environment File Setup

Create a `.env` file in your project root:

```bash
# Copy this template to .env and fill in your actual API keys

# Payment Processing
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Affiliate Tracking (optional - comment out if not using)
# SHAREASALE_MERCHANT_ID=your_id
# SHAREASALE_TOKEN=your_token
# CJ_AFFILIATE_ID=your_id
# CJ_AFFILIATE_TOKEN=your_token

# Social Media (optional - comment out if not using)
# X_CONSUMER_KEY=your_key
# X_CONSUMER_SECRET=your_secret
# X_ACCESS_TOKEN=your_token
# X_ACCESS_SECRET=your_secret
# LINKEDIN_ACCESS_TOKEN=your_token
# LINKEDIN_PERSON_ID=your_id

# Email Marketing
SENDGRID_API_KEY=your_sendgrid_key

# AI Content Generation (at least one required)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Additional integrations (optional)
# GOOGLE_SEARCH_CONSOLE_CREDENTIALS=your_credentials
# HUBSPOT_API_KEY=your_hubspot_key
```

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `.env` to your `.gitignore` file
   - Use environment-specific configuration files

2. **Use strong, unique keys**
   - Don't reuse API keys across projects
   - Rotate keys regularly

3. **Limit API key permissions**
   - Only grant necessary permissions
   - Use read-only keys where possible

4. **Monitor API usage**
   - Set up usage alerts
   - Monitor for unusual activity

## Testing Your Setup

After setting up your environment variables, you can test the integrations:

```bash
# Test payment processing
python3 -c "from REAL_PAYMENT_PROCESSING import real_payment_processing; import asyncio; asyncio.run(real_payment_processing.initialize())"

# Test affiliate tracking
python3 -c "from REAL_AFFILIATE_TRACKING import real_affiliate_tracking; import asyncio; asyncio.run(real_affiliate_tracking.initialize())"

# Test social media integration
python3 -c "from REAL_SOCIAL_MEDIA_INTEGRATION import real_social_media; import asyncio; asyncio.run(real_social_media.initialize())"
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Double-check your API keys are correct
   - Ensure keys have the necessary permissions
   - Check for typos in environment variables

2. **Rate Limiting**
   - Monitor your API usage
   - Implement exponential backoff for retries
   - Consider upgrading your API plan if needed

3. **Network Issues**
   - Check your internet connection
   - Verify firewall settings allow API calls
   - Test with a simple curl request

4. **Authentication Errors**
   - Ensure tokens haven't expired
   - Check token format and permissions
   - Verify OAuth flows if required

### Getting Help

If you encounter issues:

1. Check the logs in `logs/enhanced_automation.log`
2. Verify your API keys work with the provider's test tools
3. Check the provider's API status page for outages
4. Review the provider's documentation for any recent changes

## Next Steps

Once your environment is configured:

1. Run the enhanced automation system: `python3 ENHANCED_AUTOMATION_SYSTEM.py`
2. Monitor the logs for any integration issues
3. Start with a few key integrations and expand gradually
4. Set up monitoring and alerting for critical systems

Remember: Start with the integrations most important to your business and add others over time. Don't try to configure everything at once!