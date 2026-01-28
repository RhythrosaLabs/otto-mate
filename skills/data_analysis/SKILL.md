# Data Analysis Skill

## Description
Comprehensive data analysis capabilities for business intelligence, including e-commerce metrics, marketing performance, customer insights, and predictive analytics.

## Capabilities
- **Sales Analysis**: Revenue, orders, conversion tracking
- **Customer Segmentation**: Identify customer patterns and segments
- **Trend Identification**: Spot emerging trends in data
- **Performance Metrics**: KPI calculation and monitoring
- **Predictive Analytics**: Forecast future performance
- **A/B Testing**: Statistical analysis of experiments
- **Reporting**: Generate executive summaries and dashboards

## Tools Required
- `execute_python`
- `shopify_get_analytics`
- `shopify_list_orders`
- `printify_list_orders`
- `read_file`
- `create_file`
- `convert_format`
- `process_json`
- `search_web` (for market data)

## Workflows

### E-Commerce Performance Analysis
```yaml
name: Analyze Store Performance
steps:
  1. Fetch Shopify analytics data
  2. Fetch order history
  3. Calculate key metrics:
     - Total revenue
     - Average order value
     - Conversion rate
     - Customer acquisition cost
     - Lifetime value
  4. Identify trends (daily, weekly, monthly)
  5. Compare to previous periods
  6. Generate insights and recommendations
  7. Create visual reports

success_criteria:
  - All key metrics calculated
  - Trends identified
  - Actionable insights provided
  - Visual report generated
```

### Customer Segmentation
```yaml
name: Segment Customer Base
steps:
  1. Collect customer order data
  2. Calculate RFM metrics (Recency, Frequency, Monetary)
  3. Apply clustering algorithm
  4. Identify segments:
     - VIP customers
     - Loyal customers
     - At-risk customers
     - New customers
     - Lost customers
  5. Profile each segment
  6. Generate targeted recommendations
  7. Create segment-specific campaigns

success_criteria:
  - Clear customer segments defined
  - Each segment characterized
  - Marketing recommendations provided
```

### Product Performance Analysis
```yaml
name: Analyze Product Sales
steps:
  1. Fetch all product data
  2. Calculate metrics per product:
     - Units sold
     - Revenue generated
     - Profit margin
     - Return rate
     - Customer satisfaction
  3. Rank products by performance
  4. Identify top performers
  5. Flag underperformers
  6. Analyze seasonality
  7. Forecast future performance
  8. Generate product strategy report

success_criteria:
  - Complete product performance matrix
  - Top/bottom performers identified
  - Actionable recommendations
```

### Market Trend Analysis
```yaml
name: Analyze Market Trends
steps:
  1. Research industry trends
  2. Analyze competitor performance
  3. Identify emerging opportunities
  4. Correlate with internal data
  5. Forecast market direction
  6. Generate opportunity report

success_criteria:
  - Trend analysis complete
  - Opportunities identified
  - Competitive positioning assessed
```

## Analysis Frameworks

### AARRR (Pirate Metrics)
- **Acquisition**: Where customers come from
- **Activation**: First positive experience
- **Retention**: Customers coming back
- **Revenue**: Monetization effectiveness
- **Referral**: Viral growth coefficient

### RFM Analysis
- **Recency**: How recently did they purchase?
- **Frequency**: How often do they purchase?
- **Monetary**: How much do they spend?

### Cohort Analysis
- Group customers by signup/first purchase date
- Track behavior over time
- Identify lifecycle patterns
- Measure retention rates

## Python Analysis Scripts

### Sales Analysis Template
```python
import pandas as pd
from datetime import datetime, timedelta

def analyze_sales(orders_data):
    """Analyze sales performance"""
    df = pd.DataFrame(orders_data)
    
    # Calculate metrics
    total_revenue = df['total_price'].sum()
    total_orders = len(df)
    avg_order_value = total_revenue / total_orders
    
    # Time-based analysis
    df['date'] = pd.to_datetime(df['created_at'])
    daily_revenue = df.groupby(df['date'].dt.date)['total_price'].sum()
    
    # Product analysis
    top_products = df['line_items'].explode().groupby('product_id')['quantity'].sum().nlargest(10)
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'daily_revenue': daily_revenue.to_dict(),
        'top_products': top_products.to_dict()
    }
```

### Customer Segmentation Template
```python
def segment_customers(customer_data):
    """RFM segmentation"""
    from datetime import datetime
    
    df = pd.DataFrame(customer_data)
    today = datetime.now()
    
    # Calculate RFM
    rfm = df.groupby('customer_id').agg({
        'order_date': lambda x: (today - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        'total_price': 'sum'  # Monetary
    })
    
    rfm.columns = ['recency', 'frequency', 'monetary']
    
    # Score each metric (1-5)
    rfm['r_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1])
    rfm['f_score'] = pd.qcut(rfm['frequency'], 5, labels=[1,2,3,4,5])
    rfm['m_score'] = pd.qcut(rfm['monetary'], 5, labels=[1,2,3,4,5])
    
    # Combine scores
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # Segment definitions
    segments = {
        'VIP': rfm[rfm['rfm_score'] >= '444'],
        'Loyal': rfm[(rfm['rfm_score'] >= '333') & (rfm['rfm_score'] < '444')],
        'At Risk': rfm[(rfm['recency'] > 90) & (rfm['frequency'] > 3)],
        'New': rfm[(rfm['recency'] <= 30) & (rfm['frequency'] == 1)]
    }
    
    return segments
```

## Visualization Templates

### Revenue Dashboard
- Line chart: Revenue over time
- Bar chart: Revenue by product
- Pie chart: Revenue by category
- Heatmap: Sales by day/hour
- Gauge: Current vs target revenue

### Customer Insights
- Funnel chart: Conversion funnel
- Cohort chart: Retention rates
- Scatter plot: RFM segmentation
- Bar chart: Customer lifetime value distribution

## Reporting Templates

### Executive Summary
```markdown
# Business Performance Report
**Period**: [Date Range]

## Key Metrics
- **Total Revenue**: $X (+Y% vs last period)
- **Orders**: N (+Y% vs last period)
- **Avg Order Value**: $X (+Y% vs last period)
- **Conversion Rate**: X% (+Y% vs last period)

## Highlights
- [Key achievement 1]
- [Key achievement 2]
- [Key achievement 3]

## Concerns
- [Issue 1 and recommended action]
- [Issue 2 and recommended action]

## Recommendations
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]
```

## Error Handling

### Missing Data
- Identify gaps in data
- Estimate missing values if possible
- Flag incomplete analysis
- Request additional data

### Data Quality Issues
- Validate data ranges
- Check for outliers
- Remove duplicates
- Standardize formats

### Calculation Errors
- Validate formulas
- Check for division by zero
- Handle null values
- Log errors for review

## Best Practices
- Always validate data quality first
- Use appropriate time ranges for comparisons
- Consider seasonality in analysis
- Segment data for deeper insights
- Visualize key findings
- Provide actionable recommendations
- Update metrics regularly
- Document methodology
- Keep stakeholders informed
- Automate recurring reports

## Advanced Techniques

### Time Series Forecasting
- ARIMA models
- Seasonal decomposition
- Trend projection
- Confidence intervals

### Statistical Testing
- A/B test significance
- Chi-square tests
- Correlation analysis
- Regression models

### Machine Learning
- Churn prediction
- Customer lifetime value prediction
- Demand forecasting
- Anomaly detection

## Dependencies
- Python with pandas, numpy, scipy
- Access to analytics data
- Historical data (minimum 3 months recommended)
- Business context and goals

## Metadata
- **Domain**: analytics, business_intelligence
- **Complexity**: Medium-High
- **Automation Level**: High
- **Human Verification**: Recommended (interpret findings)
