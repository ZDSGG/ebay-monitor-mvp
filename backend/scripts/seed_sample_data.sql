INSERT INTO monitored_items (
    id,
    marketplace,
    legacy_item_id,
    url,
    note,
    status,
    title,
    currency,
    current_price,
    current_shipping_cost,
    seller_name,
    item_condition,
    availability,
    image_url,
    canonical_item_url,
    last_captured_at,
    created_at,
    updated_at
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'EBAY_US',
    '256789123456',
    'https://www.ebay.com/itm/256789123456',
    'Sample item for local development',
    'ACTIVE',
    'Sample eBay Item',
    'USD',
    199.99,
    10.00,
    'sample_seller',
    'Used',
    'IN_STOCK',
    'https://i.ebayimg.com/images/g/sample.jpg',
    'https://www.ebay.com/itm/256789123456',
    '2026-04-10T00:00:00+00:00',
    '2026-04-10T00:00:00+00:00',
    '2026-04-10T00:00:00+00:00'
);

INSERT INTO item_snapshots (
    id,
    item_id,
    price,
    shipping_cost,
    total_cost,
    capture_time,
    created_at
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    199.99,
    10.00,
    209.99,
    '2026-04-10T00:00:00+00:00',
    '2026-04-10T00:00:00+00:00'
);

INSERT INTO item_snapshots (
    id,
    item_id,
    price,
    shipping_cost,
    total_cost,
    capture_time,
    created_at
) VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    214.99,
    10.00,
    224.99,
    '2026-04-03T00:00:00+00:00',
    '2026-04-03T00:00:00+00:00'
);

INSERT INTO item_snapshots (
    id,
    item_id,
    price,
    shipping_cost,
    total_cost,
    capture_time,
    created_at
) VALUES (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    204.99,
    10.00,
    214.99,
    '2026-04-09T00:00:00+00:00',
    '2026-04-09T00:00:00+00:00'
);
