# Code Smells & Fixes

Comprehensive examples of common code smells and their refactoring solutions.

---

## 1. Long Method/Function

```diff
# BAD: 200-line function that does everything
- async function processOrder(orderId) {
-   // 50 lines: fetch order
-   // 30 lines: validate order
-   // 40 lines: calculate pricing
-   // 30 lines: update inventory
-   // 20 lines: create shipment
- }

# GOOD: Broken into focused functions
+ async function processOrder(orderId) {
+   const order = await fetchOrder(orderId);
+   validateOrder(order);
+   const pricing = calculatePricing(order);
+   await updateInventory(order);
+   const shipment = await createShipment(order);
+   return { order, pricing, shipment };
+ }
```

---

## 2. Duplicated Code

```diff
# BAD: Same logic in multiple places
- function calculateUserDiscount(user) {
-   if (user.membership === 'gold') return user.total * 0.2;
-   if (user.membership === 'silver') return user.total * 0.1;
-   return 0;
- }
-
- function calculateOrderDiscount(order) {
-   if (order.user.membership === 'gold') return order.total * 0.2;
-   if (order.user.membership === 'silver') return order.total * 0.1;
-   return 0;
- }

# GOOD: Extract common logic
+ function getMembershipDiscountRate(membership) {
+   const rates = { gold: 0.2, silver: 0.1 };
+   return rates[membership] || 0;
+ }
+
+ function calculateUserDiscount(user) {
+   return user.total * getMembershipDiscountRate(user.membership);
+ }
```

---

## 3. Large Class/Module

```diff
# BAD: God object that knows too much
- class UserManager {
-   createUser() { /* ... */ }
-   updateUser() { /* ... */ }
-   sendEmail() { /* ... */ }
-   generateReport() { /* ... */ }
-   handlePayment() { /* ... */ }
-   // 50 more methods...
- }

# GOOD: Single responsibility per class
+ class UserService {
+   create(data) { /* ... */ }
+   update(id, data) { /* ... */ }
+ }
+
+ class EmailService {
+   send(to, subject, body) { /* ... */ }
+ }
+
+ class PaymentService {
+   process(amount, method) { /* ... */ }
+ }
```

---

## 4. Long Parameter List

```diff
# BAD: Too many parameters
- function createUser(email, password, name, age, address, city, country, phone) {
-   /* ... */
- }

# GOOD: Group related parameters
+ interface UserData {
+   email: string;
+   password: string;
+   name: string;
+   age?: number;
+   address?: Address;
+ }
+
+ function createUser(data: UserData) {
+   /* ... */
+ }
```

---

## 5. Nested Conditionals

```diff
# BAD: Arrow code
- function process(order) {
-   if (order) {
-     if (order.user) {
-       if (order.user.isActive) {
-         if (order.total > 0) {
-           return processOrder(order);
-         }
-       }
-     }
-   }
- }

# GOOD: Guard clauses / early returns
+ function process(order) {
+   if (!order) return { error: 'No order' };
+   if (!order.user) return { error: 'No user' };
+   if (!order.user.isActive) return { error: 'User inactive' };
+   if (order.total <= 0) return { error: 'Invalid total' };
+   return processOrder(order);
+ }
```

---

## 6. Magic Numbers/Strings

```diff
# BAD: Unexplained values
- if (user.status === 2) { /* ... */ }
- const discount = total * 0.15;
- setTimeout(callback, 86400000);

# GOOD: Named constants
+ const UserStatus = { ACTIVE: 1, INACTIVE: 2, SUSPENDED: 3 };
+ const DISCOUNT_RATES = { STANDARD: 0.1, PREMIUM: 0.15, VIP: 0.2 };
+ const ONE_DAY_MS = 24 * 60 * 60 * 1000;
+
+ if (user.status === UserStatus.INACTIVE) { /* ... */ }
+ const discount = total * DISCOUNT_RATES.PREMIUM;
+ setTimeout(callback, ONE_DAY_MS);
```

---

## 7. Feature Envy

```diff
# BAD: Method uses another object's data more than its own
- class Order {
-   calculateDiscount(user) {
-     if (user.membershipLevel === 'gold') return this.total * 0.2;
-     if (user.accountAge > 365) return this.total * 0.1;
-     return 0;
-   }
- }

# GOOD: Move logic to the object that owns the data
+ class User {
+   getDiscountRate() {
+     if (this.membershipLevel === 'gold') return 0.2;
+     if (this.accountAge > 365) return 0.1;
+     return 0;
+   }
+ }
+
+ class Order {
+   calculateDiscount(user) {
+     return this.total * user.getDiscountRate();
+   }
+ }
```

---

## 8. Dead Code

```diff
# BAD: Unused code lingers
- function oldImplementation() { /* ... */ }
- const DEPRECATED_VALUE = 5;
- // Commented out code
- // function oldCode() { /* ... */ }

# GOOD: Remove it
+ // Delete unused functions, imports, and commented code
+ // If you need it again, git history has it
```

---

## 9. Primitive Obsession

```diff
# BAD: Using primitives for domain concepts
- function sendEmail(to, subject, body) { /* ... */ }
- sendEmail('user@example.com', 'Hello', '...');

# GOOD: Use domain types (Value Objects)
+ class Email {
+   private constructor(public readonly value: string) {
+     if (!Email.isValid(value)) throw new Error('Invalid email');
+   }
+   static create(value: string) { return new Email(value); }
+   static isValid(email: string) {
+     return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
+   }
+ }
+
+ function sendEmail(to: Email, subject: string, body: string) { /* ... */ }
+ sendEmail(Email.create('user@example.com'), 'Hello', '...');
```

---

## 10. Inappropriate Intimacy (Law of Demeter)

```diff
# BAD: One class reaches deep into another
- class OrderProcessor {
-   process(order) {
-     order.user.profile.address.street;  // Too intimate
-     order.repository.connection.config;  // Breaking encapsulation
-   }
- }

# GOOD: Ask, don't tell
+ class OrderProcessor {
+   process(order) {
+     order.getShippingAddress();  // Order knows how to get it
+     order.save();  // Order knows how to save itself
+   }
+ }
```

---

## Introducing Type Safety

```diff
# Before: No types, easy to misuse
- function calculateDiscount(user, total, membership, date) {
-   if (membership === 'gold' && date.getDay() === 5) {
-     return total * 0.25;
-   }
-   if (membership === 'gold') return total * 0.2;
-   return total * 0.1;
- }

# After: Full type safety with clear contracts
+ type Membership = 'bronze' | 'silver' | 'gold';
+
+ interface User {
+   id: string;
+   name: string;
+   membership: Membership;
+ }
+
+ interface DiscountResult {
+   original: number;
+   discount: number;
+   final: number;
+   rate: number;
+ }
+
+ function calculateDiscount(
+   user: User,
+   total: number,
+   date: Date = new Date()
+ ): DiscountResult {
+   if (total < 0) throw new Error('Total cannot be negative');
+
+   let rate = 0.1; // Default bronze
+   if (user.membership === 'gold' && date.getDay() === 5) {
+     rate = 0.25; // Friday bonus
+   } else if (user.membership === 'gold') {
+     rate = 0.2;
+   } else if (user.membership === 'silver') {
+     rate = 0.15;
+   }
+
+   return {
+     original: total,
+     discount: total * rate,
+     final: total - (total * rate),
+     rate
+   };
+ }
```
