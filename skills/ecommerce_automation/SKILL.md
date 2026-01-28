# E-Commerce Automation Skill

## Description
Complete e-commerce automation from product creation to publishing and order management across Printify and Shopify platforms.

## Capabilities
- **Product Lifecycle Management**: Create, publish, and manage products across platforms
- **Inventory Synchronization**: Keep inventory consistent between Printify and Shopify
- **Order Fulfillment**: Automated order processing and tracking
- **Pricing Optimization**: Dynamic pricing based on costs and competition
- **Collection Management**: Organize products into targeted collections

## Tools Required
- `printify_create_product`
- `printify_publish_product`
- `printify_list_products`
- `printify_get_product`
- `printify_upload_image`
- `shopify_create_product`
- `shopify_list_products`
- `shopify_update_product`
- `shopify_update_inventory`
- `shopify_add_to_collection`
- `shopify_list_orders`
- `shopify_get_order`

## Workflows

### Create & Publish Product
```yaml
name: Create and Publish Product
steps:
  1. Generate or receive product design image
  2. Upload image to Printify
  3. Create product in Printify with proper variants
  4. Publish Printify product to Shopify
  5. Verify product appears in Shopify
  6. Add to appropriate collection
  7. Set SEO metadata

success_criteria:
  - Product visible in both Printify and Shopify
  - All variants properly configured
  - Images display correctly
  - SEO fields populated
```

### Bulk Product Launch
```yaml
name: Launch Product Line
steps:
  1. Create multiple designs (use image_generation skill)
  2. For each design:
     - Upload to Printify
     - Create product with variants
     - Publish to Shopify
     - Add to collection
  3. Create bundle/collection page
  4. Generate marketing content

success_criteria:
  - All products published
  - Collection properly organized
  - Marketing materials ready
```

### Inventory Sync
```yaml
name: Synchronize Inventory
steps:
  1. Get Printify product list
  2. Get Shopify product list
  3. Compare inventory levels
  4. Update mismatches
  5. Flag out-of-stock items

success_criteria:
  - Inventory matches across platforms
  - No oversold items
```

## Error Handling

### Common Issues
1. **Image Upload Failure**
   - Retry with smaller image size
   - Convert format if needed
   - Use CDN fallback

2. **Publishing Failure**
   - Verify Shopify connection active
   - Check product has all required fields
   - Ensure variants have prices
   - Retry with exponential backoff

3. **Missing Variants**
   - Query print provider for available sizes
   - Set default variant configuration
   - Update product after creation

## Best Practices
- Always verify image upload success before product creation
- Use consistent naming conventions
- Set profit margins in metadata
- Track SKUs properly
- Test on single product before bulk operations
- Keep product descriptions SEO-optimized
- Monitor order status regularly

## Dependencies
- Valid Printify API credentials
- Active Printify shop
- Shopify store connected to Printify
- Image generation or source capability

## Metadata
- **Domain**: ecommerce
- **Complexity**: High
- **Automation Level**: Full
- **Human Verification**: Optional (recommended for first run)
