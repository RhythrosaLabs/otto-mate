# Analytics & Insights Tools

Otto now has comprehensive analytics capabilities to READ data from your Shopify and Printify stores, not just push/create products.

## New Analytics Tools

### Shopify Analytics

#### 1. **shopify_get_top_products**
Analyzes recent orders to determine which products sell best.

**Usage:**
```
"What's my top selling item?"
"Show me my best-selling products"
"Which products sell the most?"
```

**Returns:**
- Top products ranked by units sold
- Total revenue per product
- Order count per product
- Average order value
- Number of orders analyzed

**Parameters:**
- `limit`: Number of top products to return (default: 10)
- `orders_to_analyze`: Number of recent orders to analyze (default: 250)

---

#### 2. **shopify_get_product_performance**
Get detailed performance metrics for a specific product.

**Usage:**
```
"How is product [ID] performing?"
"Show me sales data for [product name]"
"Get performance metrics for product [ID]"
```

**Returns:**
- Product title, type, vendor
- Units sold
- Total revenue
- Order count
- Average order value
- Recent order history
- Created/updated dates

**Parameters:**
- `product_id`: The Shopify product ID
- `orders_to_analyze`: Number of recent orders to analyze (default: 250)

---

#### 3. **shopify_get_sales_summary**
Get comprehensive sales summary with detailed metrics.

**Usage:**
```
"Show me my sales summary"
"What's my total revenue?"
"Give me a sales overview"
```

**Returns:**
- Total orders
- Total revenue
- Average order value
- Order status breakdown (paid, pending, refunded)
- Top 5 customers by spending
- Date range of analyzed orders

**Parameters:**
- `orders_to_analyze`: Number of recent orders to analyze (default: 250)

---

### Printify Analytics

#### 1. **printify_get_top_products**
Analyze Printify orders to find top-selling products.

**Usage:**
```
"What are my best-selling Printify products?"
"Show me top products from Printify"
```

**Returns:**
- Top products ranked by units sold
- Order count per product
- Total unique products found
- Number of orders analyzed

**Parameters:**
- `limit`: Number of top products to return (default: 10)
- `max_pages`: Number of order pages to analyze (default: 5, 50 orders per page)

---

#### 2. **printify_get_product_stats**
Get detailed statistics for a specific Printify product.

**Usage:**
```
"Show me stats for Printify product [ID]"
"How is [product name] doing on Printify?"
```

**Returns:**
- Product title
- Units sold
- Order count
- Product status
- Recent order history

**Parameters:**
- `product_id`: The Printify product ID
- `max_pages`: Number of order pages to analyze (default: 5)

---

#### 3. **printify_get_shop_stats**
Get overall shop statistics from Printify.

**Usage:**
```
"Show me my Printify shop stats"
"What's my Printify overview?"
```

**Returns:**
- Total products
- Total orders
- Total items sold
- Order status breakdown
- Products by status (published/draft)

**Parameters:**
- `max_pages`: Number of pages to analyze for orders (default: 5)

---

#### 4. **printify_get_order**
Get details of a specific Printify order.

**Usage:**
```
"Show me Printify order [ID]"
"Get details for order [ID]"
```

**Returns:**
- Complete order details including line items, status, customer info

**Parameters:**
- `order_id`: The Printify order ID

---

## Example Queries You Can Now Ask

1. **"What's my top selling item?"**
   - Uses `shopify_get_top_products` to analyze orders
   - Returns ranked list with sales data

2. **"What type of products are most viewed?"**
   - Note: Shopify doesn't provide view/traffic data via API
   - Uses order data as proxy for popularity
   - Can analyze product types from top sellers

3. **"Show me my best sellers this month"**
   - Analyzes recent orders (configurable time range)
   - Returns top products with revenue data

4. **"How much revenue have I made?"**
   - Uses `shopify_get_sales_summary`
   - Returns total revenue, order count, average order value

5. **"Which products sell best on Printify vs Shopify?"**
   - Compares analytics from both platforms
   - Shows cross-platform performance

6. **"Who are my top customers?"**
   - Uses `shopify_get_sales_summary`
   - Returns top 5 customers by total spending

---

## Technical Details

### Data Sources
- **Shopify:** Uses Orders API to analyze line items
- **Printify:** Uses Orders API to analyze fulfillment data

### Analysis Methods
- Aggregates order line items by product ID
- Calculates units sold, revenue, order frequency
- Sorts by configurable metrics (sales, revenue, orders)
- Provides time-based filtering through order limits

### Performance
- Default analysis: 250 recent Shopify orders
- Default analysis: 250 Printify orders (5 pages × 50)
- Configurable limits to balance speed vs accuracy
- Results cached during conversation session

### Limitations
1. **No view/traffic data:** Shopify API doesn't provide page view analytics
   - Solution: Use order data as proxy for popularity
   - Alternative: Shopify Reports API (requires additional setup)

2. **Time range filtering:** Limited to "recent N orders"
   - Solution: Orders are returned newest-first
   - Can approximate time ranges by order volume

3. **Rate limits:** Both APIs have rate limits
   - Solution: Background task system handles retries
   - Automatic backoff for rate limit errors

---

## Integration with Otto

Otto's planning agent automatically selects the appropriate analytics tool based on your query:

- "top selling" → `shopify_get_top_products`
- "product performance" → `shopify_get_product_performance`
- "sales summary" → `shopify_get_sales_summary`
- "Printify stats" → `printify_get_shop_stats`

The execution agent handles:
- API authentication
- Rate limit retries (background tasks)
- Data aggregation
- Error handling
- Result formatting

---

## Next Steps

To add more advanced analytics:

1. **Shopify Reports API:**
   - Traffic/view data
   - Conversion rates
   - Cart abandonment

2. **Time-based filtering:**
   - Orders by date range
   - Month-over-month comparisons
   - Trend analysis

3. **Cross-platform insights:**
   - Revenue comparison tools
   - Product performance across channels
   - Inventory synchronization

4. **Customer analytics:**
   - Lifetime value (LTV)
   - Cohort analysis
   - Purchase patterns

5. **Product recommendations:**
   - Frequently bought together
   - Product affinity analysis
   - Upsell opportunities
