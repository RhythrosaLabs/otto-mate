# Email Marketing Skill

## Description
Complete email marketing automation including campaign creation, list management, personalization, A/B testing, and analytics.

## Capabilities
- **Campaign Creation**: Design and write email campaigns
- **List Segmentation**: Target specific customer groups
- **Personalization**: Dynamic content per recipient
- **Automation**: Drip campaigns and triggers
- **A/B Testing**: Test subject lines and content
- **Analytics**: Track opens, clicks, conversions

## Tools Required
- `generate_email_campaign`
- `generate_ad_copy` (for subject lines)
- `shopify_list_orders` (for customer data)
- `execute_python` (for list processing)
- `create_file` (for campaign exports)

## Workflows

### Welcome Email Series
```yaml
name: New Customer Welcome Series
triggers:
  - First purchase completed
steps:
  1. Send immediate welcome email (within 5 minutes)
  2. Wait 2 days
  3. Send product tips email
  4. Wait 3 days
  5. Send social media follow request
  6. Wait 5 days
  7. Send discount for next purchase

emails:
  1. Welcome:
     - Thank you message
     - Order confirmation
     - Brand story
     - Social links
  
  2. Tips:
     - How to use product
     - Care instructions
     - Style ideas
  
  3. Community:
     - Join Instagram
     - Share user photos
     - Hashtag campaign
  
  4. Incentive:
     - 15% off next order
     - Expires in 7 days
     - Product recommendations

success_criteria:
  - 40%+ open rate
  - 10%+ click rate
  - 5%+ conversion rate
```

### Cart Abandonment
```yaml
name: Recover Abandoned Carts
trigger:
  - Cart created but not purchased (1 hour)

steps:
  1. Wait 1 hour after abandonment
  2. Send first reminder (friendly)
  3. Wait 24 hours
  4. Send second email (with discount)
  5. Wait 48 hours
  6. Send final email (urgency + discount)

emails:
  1. Reminder (1 hour):
     - Subject: "You forgot something! 👀"
     - Show cart items
     - One-click checkout link
     - Free shipping reminder
  
  2. Incentive (24 hours):
     - Subject: "Come back! Here's 10% off 🎁"
     - 10% discount code
     - Cart items with discount shown
     - Customer reviews
  
  3. Last Chance (72 hours):
     - Subject: "Last chance: 15% off expires tonight! ⏰"
     - 15% discount code
     - Urgency messaging
     - Limited time offer

success_criteria:
  - 25%+ open rate
  - 15% cart recovery rate
  - Positive ROI
```

### Product Launch Campaign
```yaml
name: New Product Launch Email
steps:
  1. Segment customer list:
     - VIP customers (first access)
     - Past purchasers (early access)
     - General list (main launch)
  
  2. Create teaser campaign (1 week before)
  3. Send VIP exclusive (3 days before)
  4. Send early access (1 day before)
  5. Send main launch email
  6. Send reminder (3 days after)
  7. Send final call (7 days after)

success_criteria:
  - 35%+ open rate
  - 15%+ click rate
  - 50+ sales from email
```

## Email Templates

### Welcome Email
```html
Subject: Welcome to [Brand]! Here's what's next...

Hi [First Name]! 👋

Thank you for your order! We're thrilled to have you as part of the [Brand] family.

Your order #[Order Number] is confirmed and will ship within 1-2 business days.

WHAT'S NEXT?
✓ Track your order: [Tracking Link]
✓ Follow us on Instagram: @[handle]
✓ Join our community: [Link]

EXCLUSIVE OFFER
Here's 15% off your next order: [Code]
Valid for 30 days

Questions? Reply to this email anytime!

Cheers,
The [Brand] Team

[Social Links] | [Unsubscribe]
```

### Cart Abandonment
```html
Subject: You forgot something! 👀

Hi [First Name],

You left these items in your cart:

[Product Image] [Product Name]
$[Price]
[One-Click Checkout Button]

FREE SHIPPING on orders over $50!

[Continue Shopping Button]

Need help? Reply to this email or chat with us.

Happy shopping!
[Brand]

[Unsubscribe]
```

### Product Launch
```html
Subject: 🚨 NEW: [Product Name] is here!

Hi [First Name]!

The wait is over! We're excited to introduce [Product Name].

[Hero Product Image]

[Compelling product description with benefits]

✓ [Feature 1]
✓ [Feature 2]
✓ [Feature 3]

LAUNCH SPECIAL
Get 20% off with code LAUNCH20
Only available for 48 hours!

[Shop Now Button]

[Social Proof: Customer Reviews/Testimonials]

See you in the store!
[Brand]

[Social Links] | [Unsubscribe]
```

### Win-Back Campaign
```html
Subject: We miss you! Here's 25% off to come back ❤️

Hi [First Name],

It's been a while since your last order...

We've missed you! Here's what's new:

[New Product 1 Image]
[New Product 2 Image]
[New Product 3 Image]

SPECIAL WELCOME BACK OFFER
Get 25% off your next order
Code: WELCOME25
Expires in 7 days

[Shop Now Button]

We'd love to have you back!
[Brand]

[Unsubscribe]
```

## List Segmentation Strategies

### By Purchase Behavior
- **VIP**: 3+ purchases, high AOV
- **Loyal**: 2+ purchases, engaged
- **One-time**: Single purchase
- **Window shoppers**: Browsed, no purchase
- **Cart abandoners**: Added to cart, no purchase

### By Engagement
- **Highly Engaged**: Opens 50%+ of emails
- **Moderately Engaged**: Opens 25-50%
- **Low Engagement**: Opens <25%
- **Inactive**: No opens in 90 days

### By Product Interest
- **Category Browsers**: By product type viewed
- **Price Point**: Budget vs premium
- **Style Preference**: Based on purchases
- **Seasonal**: Holiday shoppers, etc.

### By Demographics
- **Location**: For shipping/local offers
- **Age/Gender**: If collected
- **Language**: For internationalization

## Personalization Techniques

### Dynamic Content
- First name in subject and body
- Product recommendations based on history
- Location-specific offers
- Birthday/anniversary emails
- Cart contents in abandonment emails
- Recently viewed items

### Behavioral Triggers
- Welcome series (first purchase)
- Re-engagement (no purchase in X days)
- Win-back (inactive for 90+ days)
- Upsell (after first purchase)
- Cross-sell (complementary products)
- Review request (after delivery)

## A/B Testing Framework

### Subject Line Tests
```yaml
Variables to test:
  - Length (short vs long)
  - Emoji usage
  - Personalization
  - Urgency language
  - Question vs statement
  - Numbers vs words

Example:
  A: "New arrivals you'll love"
  B: "🔥 50 new products just dropped"
  
Winner: Highest open rate
```

### Content Tests
```yaml
Variables to test:
  - Email length
  - Image vs text ratio
  - CTA button text
  - CTA button color
  - Product layout
  - Discount amount

Example:
  A: Single product focus
  B: Product grid (3 items)
  
Winner: Highest click-through rate
```

### Send Time Tests
```yaml
Variables to test:
  - Day of week
  - Time of day
  - Frequency
  
Optimal times to test:
  - Tuesday 10 AM
  - Wednesday 2 PM
  - Thursday 8 AM
  - Saturday 9 AM
  
Winner: Highest engagement
```

## Email Best Practices

### Design
- Mobile-first (60%+ open on mobile)
- Single column layout
- Large, tappable buttons (44px minimum)
- Scannable content (short paragraphs)
- Generous white space
- Brand consistent
- Alt text for images
- Dark mode compatible

### Copy
- Compelling subject line (40-50 characters)
- Pre-header text (90-140 characters)
- Clear value proposition
- Scannable with bullets/headers
- Conversational tone
- Single clear CTA
- Urgency/scarcity when appropriate
- Proofread thoroughly

### Technical
- Authenticated domain (SPF, DKIM, DMARC)
- Plain text version
- Unsubscribe link (required)
- Physical address (required)
- Mobile responsive
- Fast load time (<3 seconds)
- Tested across email clients
- Proper list hygiene

## Email Metrics

### Primary Metrics
- **Open Rate**: % of recipients who opened
  - Good: 20-25%
  - Great: 30%+

- **Click Rate**: % who clicked a link
  - Good: 2-3%
  - Great: 5%+

- **Conversion Rate**: % who made purchase
  - Good: 1-2%
  - Great: 3%+

- **Bounce Rate**: % undelivered
  - Acceptable: <2%
  - Red flag: >5%

- **Unsubscribe Rate**: % who opted out
  - Acceptable: <0.5%
  - Red flag: >1%

### Advanced Metrics
- Revenue per email
- List growth rate
- Share/forward rate
- ROI per campaign
- Lifetime value of email subscribers

## Compliance

### CAN-SPAM Requirements
- ✓ Accurate "From" name
- ✓ Honest subject line
- ✓ Identify as advertisement (if applicable)
- ✓ Valid physical address
- ✓ Clear unsubscribe method
- ✓ Honor opt-outs within 10 days

### GDPR (if EU customers)
- ✓ Explicit consent
- ✓ Right to access data
- ✓ Right to be forgotten
- ✓ Data protection measures
- ✓ Clear privacy policy

## Automation Sequences

### Drip Campaign Structure
```yaml
Day 0: Welcome + offer
Day 2: Value content (tips, how-to)
Day 5: Social proof (reviews)
Day 7: Product showcase
Day 10: Urgency (limited time offer)
Day 14: FAQ/objection handling
Day 21: Final push with discount
```

### Lifecycle Emails
```yaml
Onboarding: Days 0-30
  - Welcome series
  - Product education
  - Community building

Engagement: Days 31-90
  - Regular content
  - Product updates
  - Special offers

Retention: Days 91-180
  - Loyalty rewards
  - Exclusive access
  - Re-engagement campaigns

Win-Back: Day 180+
  - We miss you
  - Special comeback offer
  - Survey (why inactive)
```

## Error Handling

### High Bounce Rate
- Clean email list
- Verify email addresses
- Remove invalid emails
- Check email authentication

### Low Open Rate
- Test subject lines
- Check send time
- Review sender name
- Segment list better
- Clean inactive subscribers

### High Unsubscribe Rate
- Reduce frequency
- Improve relevance
- Segment better
- Check content quality
- Offer preference center

## Best Practices
- Build list organically (no buying)
- Double opt-in recommended
- Regular list cleaning
- Segment aggressively
- Personalize everything
- Test constantly
- Monitor metrics closely
- Respect unsubscribes immediately
- Provide value in every email
- Mobile-first design
- Consistent sending schedule
- Brand voice throughout

## Dependencies
- Email service provider (ESP)
- Customer data/CRM
- Email templates
- Analytics tracking
- Legal compliance

## Metadata
- **Domain**: marketing
- **Complexity**: Medium
- **Automation Level**: High
- **Human Verification**: Recommended (first campaign)
