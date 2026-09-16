# Async/Await Migration Patterns

Step-by-step guide for migrating callback-based code to Promises and async/await.

---

## Migration Path

```
Callbacks → Promises → async/await
```

Migrate in order. Don't skip from callbacks directly to async/await — the Promise step ensures each function's contract is correct.

---

## Step 1: Callback to Promise

```diff
# Before: Callback pattern
- function fetchUser(id, callback) {
-   db.query('SELECT * FROM users WHERE id = ?', [id], (err, rows) => {
-     if (err) return callback(err);
-     callback(null, rows[0]);
-   });
- }
-
- fetchUser(123, (err, user) => {
-   if (err) console.error(err);
-   console.log(user);
- });

# After: Promise wrapper
+ function fetchUser(id) {
+   return new Promise((resolve, reject) => {
+     db.query('SELECT * FROM users WHERE id = ?', [id], (err, rows) => {
+       if (err) return reject(err);
+       resolve(rows[0]);
+     });
+   });
+ }
+
+ fetchUser(123)
+   .then(user => console.log(user))
+   .catch(err => console.error(err));
```

**Key rules:**
- Wrap the entire callback function body in `new Promise()`
- `callback(err)` becomes `reject(err)`
- `callback(null, result)` becomes `resolve(result)`
- Keep the same function signature minus the callback parameter

---

## Step 2: Promise to async/await

```diff
# Before: Promise chains
- function processOrder(orderId) {
-   return fetchOrder(orderId)
-     .then(order => validateOrder(order))
-     .then(validOrder => calculateTotal(validOrder))
-     .then(total => chargePayment(total))
-     .then(payment => createShipment(payment))
-     .catch(err => {
-       console.error('Order processing failed:', err);
-       throw err;
-     });
- }

# After: async/await
+ async function processOrder(orderId) {
+   try {
+     const order = await fetchOrder(orderId);
+     const validOrder = await validateOrder(order);
+     const total = await calculateTotal(validOrder);
+     const payment = await chargePayment(total);
+     return await createShipment(payment);
+   } catch (err) {
+     console.error('Order processing failed:', err);
+     throw err;
+   }
+ }
```

**Key rules:**
- Add `async` to the function declaration
- Replace `.then(result =>` with `const result = await`
- Replace `.catch(err =>` with `try/catch`
- The function now returns a Promise implicitly

---

## Step 3: Parallelize independent operations

```diff
# Before: Sequential (slow — each waits for the previous)
- async function getUserDashboard(userId) {
-   const profile = await fetchProfile(userId);
-   const orders = await fetchOrders(userId);
-   const notifications = await fetchNotifications(userId);
-   return { profile, orders, notifications };
- }

# After: Parallel (fast — all three run simultaneously)
+ async function getUserDashboard(userId) {
+   const [profile, orders, notifications] = await Promise.all([
+     fetchProfile(userId),
+     fetchOrders(userId),
+     fetchNotifications(userId),
+   ]);
+   return { profile, orders, notifications };
+ }
```

**Use `Promise.all` when:** operations are independent (none needs another's result).
**Keep sequential when:** operation B depends on operation A's result.

---

## Common Pitfalls

### Pitfall 1: Forgetting to await

```javascript
// BUG: Returns a Promise, not the value
async function getUser(id) {
  const user = fetchUser(id); // Missing await!
  return user.name; // TypeError: Cannot read property 'name' of Promise
}
```

### Pitfall 2: await in loops (sequential when parallel is possible)

```diff
# Before: Sequential — processes one at a time
- async function processAll(items) {
-   const results = [];
-   for (const item of items) {
-     results.push(await processItem(item));
-   }
-   return results;
- }

# After: Parallel — processes all at once
+ async function processAll(items) {
+   return Promise.all(items.map(item => processItem(item)));
+ }
```

### Pitfall 3: Swallowing errors

```diff
# Before: Error silently disappears
- async function save(data) {
-   try {
-     await db.save(data);
-   } catch (err) {
-     console.log(err); // Logged but caller never knows it failed
-   }
- }

# After: Rethrow or return error status
+ async function save(data) {
+   try {
+     await db.save(data);
+     return { success: true };
+   } catch (err) {
+     console.error('Save failed:', err);
+     return { success: false, error: err.message };
+   }
+ }
```

---

## Migration Checklist

- [ ] Identify all callback-based functions (grep for `callback`, `cb`, `done` parameters)
- [ ] Wrap each in Promise (Step 1) — test after each conversion
- [ ] Convert Promise chains to async/await (Step 2) — test after each conversion
- [ ] Identify parallelizable operations (Step 3) — test after each change
- [ ] Update callers to handle the new Promise-based return values
- [ ] Remove any `util.promisify` wrappers if you wrote native Promises
- [ ] Verify error propagation: errors should reach the top-level handler
