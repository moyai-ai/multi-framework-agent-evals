-- Seed Data for Relational Data Agent Demo
-- This SQL script populates the database with sample data

-- Clear existing data
DELETE FROM inventory_logs;
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;

-- Insert Customers
INSERT INTO customers (id, name, email, phone, address, city, country, created_at, is_active) VALUES
(1, 'Alice Johnson', 'alice@example.com', '+1-555-0101', '123 Main St', 'New York', 'USA', '2023-01-15', 1),
(2, 'Bob Smith', 'bob@example.com', '+1-555-0102', '456 Oak Ave', 'Los Angeles', 'USA', '2023-02-20', 1),
(3, 'Carol Williams', 'carol@example.com', '+1-555-0103', '789 Pine Rd', 'Chicago', 'USA', '2023-03-10', 1),
(4, 'David Brown', 'david@example.com', '+1-555-0104', '321 Elm St', 'Houston', 'USA', '2023-04-05', 1),
(5, 'Emma Davis', 'emma@example.com', '+1-555-0105', '654 Maple Dr', 'Phoenix', 'USA', '2023-05-12', 1),
(6, 'Frank Miller', 'frank@example.com', '+1-555-0106', '987 Cedar Ln', 'Philadelphia', 'USA', '2023-06-18', 1),
(7, 'Grace Wilson', 'grace@example.com', '+1-555-0107', '147 Birch Blvd', 'San Antonio', 'USA', '2023-07-22', 1),
(8, 'Henry Moore', 'henry@example.com', '+1-555-0108', '258 Spruce Way', 'San Diego', 'USA', '2023-08-30', 1),
(9, 'Iris Taylor', 'iris@example.com', '+1-555-0109', '369 Willow Ct', 'Dallas', 'USA', '2023-09-14', 1),
(10, 'Jack Anderson', 'jack@example.com', '+1-555-0110', '741 Ash Ave', 'San Jose', 'USA', '2023-10-25', 0);

-- Insert Products
INSERT INTO products (id, name, category, price, stock_quantity, description, created_at) VALUES
(1, 'Laptop Pro 15', 'Electronics', 1299.99, 50, 'High-performance laptop with 15-inch display', '2023-01-01'),
(2, 'Wireless Mouse', 'Electronics', 29.99, 200, 'Ergonomic wireless mouse with precision tracking', '2023-01-01'),
(3, 'USB-C Hub', 'Electronics', 49.99, 150, 'Multi-port USB-C hub with HDMI output', '2023-01-01'),
(4, 'Mechanical Keyboard', 'Electronics', 89.99, 75, 'RGB mechanical keyboard with cherry switches', '2023-01-01'),
(5, 'Monitor 27"', 'Electronics', 399.99, 30, '4K UHD monitor with HDR support', '2023-01-01'),
(6, 'Office Chair', 'Furniture', 299.99, 40, 'Ergonomic office chair with lumbar support', '2023-01-01'),
(7, 'Standing Desk', 'Furniture', 599.99, 20, 'Electric height-adjustable standing desk', '2023-01-01'),
(8, 'Desk Lamp', 'Furniture', 39.99, 100, 'LED desk lamp with adjustable brightness', '2023-01-01'),
(9, 'Notebook Set', 'Stationery', 19.99, 300, 'Set of 5 premium notebooks', '2023-01-01'),
(10, 'Pen Pack', 'Stationery', 9.99, 500, 'Pack of 10 professional pens', '2023-01-01'),
(11, 'Webcam HD', 'Electronics', 79.99, 60, '1080p HD webcam with auto-focus', '2023-02-01'),
(12, 'Headphones', 'Electronics', 149.99, 80, 'Noise-canceling wireless headphones', '2023-02-01'),
(13, 'External SSD 1TB', 'Electronics', 129.99, 45, 'Portable SSD with USB 3.2', '2023-03-01'),
(14, 'Printer', 'Electronics', 199.99, 25, 'All-in-one wireless printer', '2023-03-01'),
(15, 'Cable Organizer', 'Accessories', 14.99, 200, 'Desktop cable management system', '2023-04-01');

-- Insert Orders
INSERT INTO orders (id, customer_id, order_date, status, total_amount, shipping_address, payment_method) VALUES
(1, 1, '2024-01-15', 'delivered', 1379.97, '123 Main St, New York', 'credit_card'),
(2, 2, '2024-01-20', 'delivered', 449.98, '456 Oak Ave, Los Angeles', 'credit_card'),
(3, 3, '2024-02-05', 'delivered', 899.97, '789 Pine Rd, Chicago', 'paypal'),
(4, 1, '2024-02-14', 'delivered', 159.98, '123 Main St, New York', 'credit_card'),
(5, 4, '2024-02-28', 'delivered', 1899.96, '321 Elm St, Houston', 'credit_card'),
(6, 5, '2024-03-10', 'delivered', 329.97, '654 Maple Dr, Phoenix', 'debit_card'),
(7, 2, '2024-03-15', 'delivered', 729.98, '456 Oak Ave, Los Angeles', 'credit_card'),
(8, 6, '2024-03-25', 'delivered', 99.97, '987 Cedar Ln, Philadelphia', 'paypal'),
(9, 7, '2024-04-01', 'delivered', 1429.97, '147 Birch Blvd, San Antonio', 'credit_card'),
(10, 3, '2024-04-10', 'delivered', 249.98, '789 Pine Rd, Chicago', 'credit_card'),
(11, 8, '2024-04-20', 'shipped', 679.97, '258 Spruce Way, San Diego', 'paypal'),
(12, 1, '2024-05-01', 'shipped', 449.97, '123 Main St, New York', 'credit_card'),
(13, 9, '2024-05-05', 'processing', 199.98, '369 Willow Ct, Dallas', 'debit_card'),
(14, 4, '2024-05-10', 'processing', 89.99, '321 Elm St, Houston', 'credit_card'),
(15, 5, '2024-05-15', 'pending', 1549.96, '654 Maple Dr, Phoenix', 'paypal'),
(16, 2, '2024-05-18', 'pending', 79.98, '456 Oak Ave, Los Angeles', 'credit_card'),
(17, 6, '2024-05-20', 'pending', 339.97, '987 Cedar Ln, Philadelphia', 'credit_card'),
(18, 3, '2024-05-22', 'pending', 599.99, '789 Pine Rd, Chicago', 'debit_card'),
(19, 7, '2024-05-23', 'pending', 149.99, '147 Birch Blvd, San Antonio', 'paypal'),
(20, 8, '2024-05-24', 'pending', 1299.99, '258 Spruce Way, San Diego', 'credit_card');

-- Insert Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- Order 1
(1, 1, 1, 1299.99, 1299.99),
(1, 2, 1, 29.99, 29.99),
(1, 3, 1, 49.99, 49.99),
-- Order 2
(2, 5, 1, 399.99, 399.99),
(2, 3, 1, 49.99, 49.99),
-- Order 3
(3, 6, 1, 299.99, 299.99),
(3, 7, 1, 599.99, 599.99),
-- Order 4
(4, 11, 2, 79.99, 159.98),
-- Order 5
(5, 1, 1, 1299.99, 1299.99),
(5, 6, 2, 299.99, 599.98),
-- Order 6
(6, 2, 3, 29.99, 89.97),
(6, 8, 2, 39.99, 79.98),
(6, 9, 8, 19.99, 159.92),
-- Order 7
(7, 13, 2, 129.99, 259.98),
(7, 4, 5, 89.99, 449.95),
(7, 10, 2, 9.99, 19.98),
-- Order 8
(8, 10, 5, 9.99, 49.95),
(8, 9, 2, 19.99, 39.98),
(8, 15, 1, 14.99, 14.99),
-- Order 9
(9, 1, 1, 1299.99, 1299.99),
(9, 13, 1, 129.99, 129.99),
-- Order 10
(10, 12, 1, 149.99, 149.99),
(10, 11, 1, 79.99, 79.99),
(10, 10, 2, 9.99, 19.98),
-- Order 11
(11, 5, 1, 399.99, 399.99),
(11, 4, 3, 89.99, 269.97),
(11, 15, 1, 14.99, 14.99),
-- Order 12
(12, 6, 1, 299.99, 299.99),
(12, 12, 1, 149.99, 149.99),
-- Order 13
(13, 14, 1, 199.99, 199.99),
-- Order 14
(14, 4, 1, 89.99, 89.99),
-- Order 15
(15, 1, 1, 1299.99, 1299.99),
(15, 3, 5, 49.99, 249.95),
-- Order 16
(16, 2, 2, 29.99, 59.98),
(16, 10, 2, 9.99, 19.98),
-- Order 17
(17, 6, 1, 299.99, 299.99),
(17, 8, 1, 39.99, 39.99),
-- Order 18
(18, 7, 1, 599.99, 599.99),
-- Order 19
(19, 12, 1, 149.99, 149.99),
-- Order 20
(20, 1, 1, 1299.99, 1299.99);

-- Insert Inventory Logs
INSERT INTO inventory_logs (product_id, change_type, quantity_change, new_quantity, timestamp, notes) VALUES
(1, 'restock', 100, 150, '2024-01-01', 'Initial stock'),
(2, 'restock', 250, 450, '2024-01-01', 'Initial stock'),
(3, 'restock', 200, 350, '2024-01-01', 'Initial stock'),
(4, 'restock', 150, 225, '2024-01-01', 'Initial stock'),
(5, 'restock', 50, 80, '2024-01-01', 'Initial stock'),
(1, 'sale', -3, 147, '2024-01-15', 'Order 1'),
(2, 'sale', -1, 449, '2024-01-15', 'Order 1'),
(3, 'sale', -1, 349, '2024-01-15', 'Order 1'),
(5, 'sale', -1, 79, '2024-01-20', 'Order 2'),
(3, 'sale', -1, 348, '2024-01-20', 'Order 2'),
(6, 'restock', 60, 100, '2024-02-01', 'Monthly restock'),
(7, 'restock', 30, 50, '2024-02-01', 'Monthly restock'),
(6, 'sale', -1, 99, '2024-02-05', 'Order 3'),
(7, 'sale', -1, 49, '2024-02-05', 'Order 3'),
(11, 'restock', 100, 160, '2024-02-10', 'New product stock'),
(11, 'sale', -2, 158, '2024-02-14', 'Order 4'),
(1, 'sale', -1, 146, '2024-02-28', 'Order 5'),
(6, 'sale', -2, 97, '2024-02-28', 'Order 5'),
(1, 'adjustment', -2, 144, '2024-03-01', 'Damaged units removed'),
(12, 'restock', 120, 200, '2024-03-01', 'New product stock'),
(13, 'restock', 80, 125, '2024-03-01', 'New product stock'),
(2, 'sale', -3, 446, '2024-03-10', 'Order 6'),
(8, 'sale', -2, 98, '2024-03-10', 'Order 6'),
(9, 'sale', -8, 292, '2024-03-10', 'Order 6'),
(13, 'sale', -2, 123, '2024-03-15', 'Order 7'),
(4, 'sale', -5, 220, '2024-03-15', 'Order 7'),
(10, 'sale', -2, 498, '2024-03-15', 'Order 7'),
(14, 'restock', 40, 65, '2024-03-20', 'New product stock'),
(15, 'restock', 250, 450, '2024-04-01', 'New product stock'),
(1, 'sale', -1, 143, '2024-04-01', 'Order 9'),
(13, 'sale', -1, 122, '2024-04-01', 'Order 9'),
(12, 'sale', -1, 199, '2024-04-10', 'Order 10'),
(11, 'sale', -1, 157, '2024-04-10', 'Order 10'),
(10, 'sale', -2, 496, '2024-04-10', 'Order 10'),
(5, 'sale', -1, 78, '2024-04-20', 'Order 11'),
(4, 'sale', -3, 217, '2024-04-20', 'Order 11'),
(15, 'sale', -1, 449, '2024-04-20', 'Order 11'),
(1, 'return', 1, 144, '2024-05-02', 'Customer return - Order 5'),
(6, 'sale', -1, 96, '2024-05-01', 'Order 12'),
(12, 'sale', -1, 198, '2024-05-01', 'Order 12'),
(14, 'sale', -1, 64, '2024-05-05', 'Order 13'),
(4, 'sale', -1, 216, '2024-05-10', 'Order 14'),
(1, 'sale', -1, 143, '2024-05-15', 'Order 15'),
(3, 'sale', -5, 343, '2024-05-15', 'Order 15');