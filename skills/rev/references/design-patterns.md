# Design Patterns for Refactoring

Common design patterns to apply when refactoring complex conditional logic.

---

## Strategy Pattern

Replace conditional logic with polymorphic strategies.

```diff
# Before: Conditional logic
- function calculateShipping(order, method) {
-   if (method === 'standard') {
-     return order.total > 50 ? 0 : 5.99;
-   } else if (method === 'express') {
-     return order.total > 100 ? 9.99 : 14.99;
-   } else if (method === 'overnight') {
-     return 29.99;
-   }
- }

# After: Strategy pattern
+ interface ShippingStrategy {
+   calculate(order: Order): number;
+ }
+
+ class StandardShipping implements ShippingStrategy {
+   calculate(order: Order) {
+     return order.total > 50 ? 0 : 5.99;
+   }
+ }
+
+ class ExpressShipping implements ShippingStrategy {
+   calculate(order: Order) {
+     return order.total > 100 ? 9.99 : 14.99;
+   }
+ }
+
+ function calculateShipping(order: Order, strategy: ShippingStrategy) {
+   return strategy.calculate(order);
+ }
```

**When to use**: Multiple algorithms/behaviors that can be swapped at runtime.

---

## Chain of Responsibility

Replace nested validation with a chain of validators.

```diff
# Before: Nested validation
- function validate(user) {
-   const errors = [];
-   if (!user.email) errors.push('Email required');
-   else if (!isValidEmail(user.email)) errors.push('Invalid email');
-   if (!user.name) errors.push('Name required');
-   if (user.age < 18) errors.push('Must be 18+');
-   return errors;
- }

# After: Chain of responsibility
+ abstract class Validator {
+   protected next?: Validator;
+   abstract doValidate(user: User): string | null;
+
+   setNext(validator: Validator): Validator {
+     this.next = validator;
+     return validator;
+   }
+
+   validate(user: User): string | null {
+     const error = this.doValidate(user);
+     if (error) return error;
+     return this.next?.validate(user) ?? null;
+   }
+ }
+
+ // Build the chain
+ const validator = new EmailRequiredValidator()
+   .setNext(new EmailFormatValidator())
+   .setNext(new NameRequiredValidator())
+   .setNext(new AgeValidator());
```

**When to use**: Sequential validation or processing where each step may short-circuit.

---

## Factory Pattern

Replace complex object creation with factory methods.

```diff
# Before: Complex constructor calls everywhere
- const user = new User(email, name, 'standard', new Date(), null, []);
- const adminUser = new User(email, name, 'admin', new Date(), null, ['admin']);

# After: Factory methods
+ class UserFactory {
+   static createStandard(email: string, name: string): User {
+     return new User(email, name, 'standard', new Date(), null, []);
+   }
+
+   static createAdmin(email: string, name: string): User {
+     return new User(email, name, 'admin', new Date(), null, ['admin']);
+   }
+ }
+
+ const user = UserFactory.createStandard(email, name);
+ const admin = UserFactory.createAdmin(email, name);
```

**When to use**: Complex object creation that should be encapsulated.

---

## Null Object Pattern

Replace null checks with a null object.

```diff
# Before: Null checks everywhere
- function getDiscount(user) {
-   if (user === null) return 0;
-   if (user.membership === null) return 0;
-   return user.membership.discountRate;
- }

# After: Null object
+ class NullMembership implements Membership {
+   get discountRate() { return 0; }
+   get benefits() { return []; }
+ }
+
+ class NullUser implements User {
+   get membership() { return new NullMembership(); }
+ }
+
+ function getDiscount(user: User) {
+   return user.membership.discountRate;  // No null checks needed
+ }
```

**When to use**: Frequently checking for null/undefined with default behavior.
