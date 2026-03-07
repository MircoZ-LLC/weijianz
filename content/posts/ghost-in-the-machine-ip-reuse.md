---
title: 'The "Ghost" in the Machine — Solving IP Reuse'
date: 2026-03-07
draft: false
tags: ['AWS', 'DynamoDB', 'Distributed Systems', 'ECS']
description: 'How we used optimistic locking to prevent stale deletes in a high-scale IP mapping service.'
showTableOfContents: true
---

In a large-scale cloud environment, resources are ephemeral. When an instance is terminated, its internal IP is released back into the pool and often reassigned to a new instance within minutes. This creates a classic **Race Condition** in our mapping service.

## The Problem: The "Stale Delete"

Imagine this scenario:

1. **Instance A** (IP: `10.0.0.1`) is marked for deprovisioning. A "Delete" task is sent to the queue.
2. The network jitters — the "Delete" task is delayed.
3. **Instance B** is launched and gets the same IP: `10.0.0.1`. It successfully registers itself in our DynamoDB mapping table.
4. The delayed "Delete" task for Instance A finally arrives.

Without a safeguard, the service would simply see a delete request for `10.0.0.1` and wipe out the new registration for Instance B. Instance B is now a **"ghost"** — it exists in the cell but is invisible to the control plane.

## The Solution: Optimistic Locking with Timestamps

To solve this, we moved away from simple "Delete by Primary Key" and implemented **Conditional Deletes**.

We introduced a `CreationTimestamp` as a mandatory attribute for every mapping entry. When a deprovisioning workflow triggers a deletion, it must include the timestamp of the specific instance it intends to destroy.

### The DynamoDB Logic

We leverage **Condition Expressions** to ensure atomicity. The deletion only executes if the timestamp in the database matches the timestamp in the request.

```json
{
    "TableName": "HostToCellMapping",
    "Key": { "HostIP": "10.0.0.1" },
    "ConditionExpression": "CreationTimestamp = :expected_ts",
    "ExpressionAttributeValues": {
        ":expected_ts": "2024-03-07T10:00:00Z"
    }
}
```

This is a single atomic operation — no "Read-Then-Delete" round trip, no window for a race condition between the read and the write.

## Handling the "Conflict"

If Instance B has already taken over the IP, the `CreationTimestamp` will not match, and DynamoDB will throw a `ConditionalCheckFailedException`.

Instead of treating this as a failure, our service interprets this as a **"Logical Success."** It means the stale record is already gone, and we successfully avoided corrupting the new instance's data. This "silent ignore" strategy prevents unnecessary alerts and keeps our system's noise level low.

## Why It Matters

- **Edge-Case Thinking** — Not just building a CRUD service, but reasoning about failure modes at scale.
- **Cost & Performance** — A single atomic operation beats a "Read-Then-Delete" approach in both latency and cost.
- **Alarm Fatigue** — Distinguishing between a true error and a logical success keeps on-call noise low. A `ConditionalCheckFailedException` here is not a bug; it's the system working correctly.
