# Quick Reference: Analytics Queries

## What You Can Ask Otto Now

### Top Sellers
```
"What's my top selling item?"
"Show me my best-selling products"
"Which products sell the most?"
"What are my top 5 products?"
```
→ Uses: `shopify_get_top_products` or `printify_get_top_products`

### Sales Overview
```
"What's my total revenue?"
"Show me my sales summary"
"How many orders have I had?"
"What's my average order value?"
```
→ Uses: `shopify_get_sales_summary`

### Product Performance
```
"How is product [ID] doing?"
"Show me sales for [product name]"
"How many units of [product] have I sold?"
```
→ Uses: `shopify_get_product_performance` or `printify_get_product_stats`

### Shop Statistics
```
"Show me my Printify stats"
"What's my shop overview?"
"How many products do I have?"
"How many orders are pending?"
```
→ Uses: `printify_get_shop_stats` or `shopify_get_analytics`

### Customer Insights
```
"Who are my top customers?"
"Show me my best customers"
"Which customers spend the most?"
```
→ Uses: `shopify_get_sales_summary` (includes top 5 customers)

### Cross-Platform Comparison
```
"Compare Shopify vs Printify sales"
"Which platform sells more?"
"Show me performance across channels"
```
→ Otto will use multiple tools and aggregate results

### Order Details
```
"Show me order [ID]"
"Get details for order [number]"
```
→ Uses: `shopify_get_order` or `printify_get_order`

## Example Responses

### Query: "What's my top selling item?"

**Otto's Response:**
```
Based on your recent 250 orders, here are your top-selling products:

1. Funny Cat Mug
   - Units sold: 45
   - Total revenue: $674.55
   - Orders: 42
   - Avg order value: $16.06

2. Cool T-Shirt Design
   - Units sold: 38
   - Total revenue: $949.50
   - Orders: 35
   - Avg order value: $27.13

3. Motivational Poster
   - Units sold: 29
   - Total revenue: $435.00
   - Orders: 25
   - Avg order value: $17.40
```

### Query: "Show me my sales summary"

**Otto's Response:**
```
Here's your sales summary based on 250 recent orders:

📊 Overall Metrics:
- Total Orders: 250
- Total Revenue: $12,450.75
- Average Order Value: $49.80

💰 Order Status:
- Paid: 230 orders
- Pending: 15 orders
- Refunded: 5 orders

👥 Top Customers:
1. customer@example.com - 8 orders, $425.50
2. buyer@test.com - 6 orders, $380.25
3. shopper@email.com - 5 orders, $315.00

📅 Date Range:
- Earliest: 2024-01-15
- Latest: 2024-01-31
```

## Important Notes

### Data Freshness
- Analyzes recent orders (default: last 250)
- Shopify orders are newest-first
- Printify: 5 pages × 50 orders = 250 orders

### Limitations
1. **No direct view/traffic data** - Shopify API doesn't provide page views
   - Use order data as proxy for popularity
   
2. **Time range filtering** - Limited to "recent N orders"
   - Can't filter by specific date ranges yet
   - Working on adding date filtering

3. **Product views** - Not available via API
   - Can infer popularity from sales
   - Shopify Reports API required for views (future enhancement)

### Performance Tips
- Default settings balance speed vs accuracy
- Increase `orders_to_analyze` for more complete data
- Be aware: more orders = slower response

## Testing

Try these queries in Otto:

1. ✅ "What's my top selling item?"
2. ✅ "Show me my sales summary"
3. ✅ "How many orders have I had?"
4. ✅ "Who are my top customers?"
5. ✅ "Show me my Printify shop stats"
6. ✅ "Compare my best sellers"

Server is running at: http://localhost:8000

## Troubleshooting

### "No orders found"
- Check Shopify/Printify credentials in config
- Verify you have orders in your store
- Check Otto logs for API errors

### "Rate limit exceeded"
- Otto's background task system will auto-retry
- Look for ⏳ indicator in UI
- Check bottom-left popup for task status

### "Product not found"
- Verify product ID is correct
- Use `list_products` to see all product IDs
- Check if product was deleted

### Slow responses
- Reduce `orders_to_analyze` parameter
- Default is 250, try 100 for faster results
- Trade-off: less complete data

## Next Enhancements

Coming soon:
- 📅 Date range filtering
- 📈 Trend analysis (growing/declining)
- 🔍 Product search/filtering
- 📊 Visual charts and graphs
- 🛒 Cart abandonment data
- 🎯 Conversion rate tracking
