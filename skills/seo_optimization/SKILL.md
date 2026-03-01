# SEO Optimization Skill

## Description
Complete SEO optimization for e-commerce stores, blog content, and digital assets with keyword research, on-page optimization, and technical SEO.

## Capabilities
- **Keyword Research**: Find high-value keywords
- **On-Page Optimization**: Optimize titles, descriptions, headers
- **Content Optimization**: SEO-friendly content creation
- **Technical SEO**: Site structure and performance
- **Competitor SEO Analysis**: Reverse engineer competitor strategies
- **Link Building**: Identify backlink opportunities

## Tools Required
- `search_web`
- `browse_url`
- `research_topic`
- `analyze_competitor`
- `generate_seo_content`
- `generate_blog_post`
- `shopify_create_product` (for SEO optimization)
- `shopify_create_blog_post`

## Workflows

### Product SEO Optimization
```yaml
name: Optimize Product for Search
steps:
  - Research keywords for product niche
  - Analyze top-ranking competitor products
  - Identify keyword opportunities
  - Optimize product title (60 chars, keyword-rich)
  - Write SEO description (155 chars)
  - Create detailed product description (500+ words)
  - Add keyword-rich alt text to images
  - Set SEO URL slug
  - Add schema markup
  - Generate internal link opportunities

success_criteria:
  - Primary keyword in title
  - Meta description under 155 characters
  - 500+ word description
  - All images have alt text
  - Clean URL structure
```

### Blog Content SEO
```yaml
name: Create SEO-Optimized Blog Post
steps:
  - Research target keyword (search volume, difficulty)
  - Analyze top 10 ranking articles
  - Identify content gaps
  - Create comprehensive outline
  - Write 1500+ word article
  - "Optimize: Title tag (keyword + modifier), Meta description, H1/H2/H3 headers with keywords, Image alt text, Internal links (3-5), External links (2-3 authority sites)"
  - Add FAQ schema
  - Create social media snippets
  - Publish and index

success_criteria:
  - 1500+ words
  - Keyword density 1-2%
  - 3+ internal links
  - All images optimized
  - Mobile-friendly
  - Fast load time (<3s)
```

### Complete Site SEO Audit
```yaml
name: Perform SEO Audit
steps:
  - Crawl site structure
  - "Analyze technical SEO: Page speed, Mobile responsiveness, SSL certificate, XML sitemap, Robots.txt"
  - "On-page analysis: Title tags, Meta descriptions, Header structure, Image optimization, Internal linking"
  - "Content analysis: Thin content, Duplicate content, Keyword targeting"
  - Competitor comparison
  - Generate prioritized fix list
  - Create implementation plan

success_criteria:
  - Complete audit report
  - Issues categorized by priority
  - Actionable recommendations
  - Expected impact estimates
```

## Keyword Research Strategies

### Keyword Types
- **Head Terms**: High volume, high competition (e.g., "t-shirts")
- **Body Terms**: Medium volume, medium competition (e.g., "funny cat t-shirts")
- **Long-Tail**: Low volume, low competition (e.g., "vintage 80s cat t-shirt for women")

### Research Process
1. Start with seed keywords
2. Use Google Autocomplete
3. Check "People Also Ask"
4. Analyze competitor keywords
5. Use keyword tools (Ahrefs, SEMrush concepts)
6. Evaluate: volume, difficulty, intent
7. Select mix of head, body, and long-tail

### Keyword Intent
- **Informational**: "how to", "what is", "guide to"
- **Navigational**: Brand names, specific sites
- **Commercial**: "best", "review", "compare"
- **Transactional**: "buy", "discount", "cheap", "order"

## On-Page SEO Checklist

### Title Tag
- ✓ Include primary keyword
- ✓ Keep under 60 characters
- ✓ Add modifiers (2024, best, guide, review)
- ✓ Brand at end (if space)
- ✓ Make compelling/clickable

### Meta Description
- ✓ Include primary keyword
- ✓ Keep 150-155 characters
- ✓ Clear call-to-action
- ✓ Describe value proposition
- ✓ Natural, readable

### URL Structure
- ✓ Short and descriptive
- ✓ Include target keyword
- ✓ Use hyphens (not underscores)
- ✓ Lowercase letters
- ✓ No special characters

### Content Optimization
- ✓ Keyword in first 100 words
- ✓ Headers (H1, H2, H3) with keywords
- ✓ Keyword density 1-2%
- ✓ LSI keywords included
- ✓ Internal links (3-5)
- ✓ External authority links (2-3)
- ✓ 1000+ words (for blog content)
- ✓ Easy to read (short paragraphs, bullets)

### Images
- ✓ Descriptive file names
- ✓ Alt text with keywords
- ✓ Compressed for speed
- ✓ Responsive sizing
- ✓ WebP format

## Technical SEO

### Site Speed
- Optimize images
- Minimize CSS/JS
- Use CDN
- Enable caching
- Lazy load images
- Target: <3 seconds load time

### Mobile Optimization
- Responsive design
- Touch-friendly buttons
- Readable text size
- Fast mobile load time
- No intrusive popups

### Site Structure
- Logical hierarchy
- XML sitemap
- Robots.txt
- Breadcrumbs
- Clean URL structure
- 301 redirects for moved content

### Schema Markup
- Product schema
- Review schema
- FAQ schema
- Breadcrumb schema
- Organization schema

## Content Templates

### Product SEO Title
```
[Keyword] | [Benefit/Feature] | [Brand] | [Modifier]

Examples:
- Funny Cat T-Shirts | 100% Cotton | CatLovers | Free Shipping
- Organic Coffee Mugs | Eco-Friendly Ceramic | HomeWare | 2024
```

### Meta Description
```
[Benefit] [Keyword] with [unique value prop]. [Social proof or feature]. [Call-to-action]!

Example:
Shop premium funny cat t-shirts with free worldwide shipping. Over 50 unique designs, 5-star rated. Order today and get 20% off!
```

### SEO-Optimized Blog Intro
```
[Hook with stat or question]

[Address reader pain point]

In this guide, you'll learn:
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

Let's dive in!
```

## Link Building Strategies

### Internal Linking
- Link from high-authority pages
- Use descriptive anchor text
- Create content hubs
- Update old content with new links
- Use breadcrumbs

### External Backlinks
- Guest post on relevant blogs
- Create shareable infographics
- Build relationships with influencers
- Get listed in directories
- Create linkable assets (tools, guides)

## Local SEO (if applicable)

### Google Business Profile
- Claim and verify listing
- Complete all information
- Add photos regularly
- Collect reviews
- Post updates

### Local Citations
- NAP consistency (Name, Address, Phone)
- List in relevant directories
- Local keywords
- Location pages

## Error Handling

### Keyword Cannibalization
- Identify competing pages
- Consolidate or differentiate
- Set canonical tags
- Update internal links

### Duplicate Content
- Use canonical tags
- 301 redirect duplicates
- Add noindex to low-value pages
- Rewrite similar content

### Broken Links
- Regular site crawl
- Fix or redirect 404s
- Update outdated external links
- Remove or replace dead links

## Best Practices
- Focus on user intent, not just keywords
- Create comprehensive content
- Update content regularly
- Build natural backlinks
- Monitor Google Search Console
- Track rankings and traffic
- Stay current with algorithm updates
- Prioritize mobile experience
- Optimize for voice search
- Use structured data
- Create content clusters
- Improve Core Web Vitals

## Measurement & Tracking

### Key Metrics
- **Organic Traffic**: Sessions from search
- **Keyword Rankings**: Position for target keywords
- **Click-Through Rate**: Impressions to clicks
- **Bounce Rate**: Single-page sessions
- **Dwell Time**: Time on page
- **Conversions**: Goals completed from organic

### Tools
- Google Search Console
- Google Analytics
- Page Speed Insights
- Mobile-Friendly Test
- Schema Markup Validator

## Dependencies
- Website access
- Content creation capability
- Competitor research tools
- Keyword research capability
- Technical SEO knowledge

## Metadata
- **Domain**: marketing, content
- **Complexity**: Medium-High
- **Automation Level**: Medium
- **Human Verification**: Recommended (content quality)
